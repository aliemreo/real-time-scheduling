#include "task_ali.cpp"

struct ScheduleEvent {
    double time;
    Job* job;
    std::string type;
    std::string description;
};

class Scheduler {
public:
    std::string name;
    double current_time = 0.0;
    std::vector<ScheduleEvent> events;
    std::vector<Job*> completed_jobs;
    std::vector<Job*> missed_deadlines;

    Scheduler(std::string n) : name(n) {}
    virtual ~Scheduler() = default;

    // Pure virtual function to select a task
    virtual Job* select_task(const std::vector<Job*>& ready_queue) = 0;

    void reset() {
        current_time = 0;
        events.clear();
        completed_jobs.clear();
        missed_deadlines.clear();
    }

    void add_event(double time, Job* job, const std::string& type, const std::string& desc = "") {
        events.push_back({time, job, type, desc});
        // std::cout << "[" << time << "] " << type << " " << (job ? "Job" : "IDLE") << "\n"; 
    }

    SchedulerStats get_statistics() {
        SchedulerStats stats;
        stats.scheduler_name = name;
        stats.completed = completed_jobs.size();
        stats.missed = missed_deadlines.size();
        stats.total_tasks = stats.completed + stats.missed;
        stats.success_rate = (stats.total_tasks == 0) ? 0.0 : (double)stats.completed / stats.total_tasks * 100.0;

        double total_response = 0;
        double total_completion = 0;
        stats.max_response_time = 0;

        for (auto* job : completed_jobs) {
            double response = job->start_time - job->current_release;
            double completion = job->completion_time - job->current_release;
            
            total_response += response;
            total_completion += completion;
            if (response > stats.max_response_time) stats.max_response_time = response;
        }

        if (stats.completed > 0) {
            stats.avg_response_time = total_response / stats.completed;
            stats.avg_completion_time = total_completion / stats.completed;
        }
        return stats;
    }
};

// --- Specific Schedulers ---

// 1. Rate Monotonic (RM)
class RateMonotonicScheduler : public Scheduler {
public:
    RateMonotonicScheduler() : Scheduler("Rate Monotonic (RM)") {}

    Job* select_task(const std::vector<Job*>& ready_queue) override {
        if (ready_queue.empty()) return nullptr;
        
        // Min period (periodic/dynamic only), others infinite
        auto it = std::min_element(ready_queue.begin(), ready_queue.end(), 
            [](const Job* a, const Job* b) {
                double pa = (a->task->type == PERIODIC || a->task->type == DYNAMIC) ? a->task->period : 1e99;
                double pb = (b->task->type == PERIODIC || b->task->type == DYNAMIC) ? b->task->period : 1e99;
                return pa < pb;
            });
        return *it;
    }
};

// 2. Earliest Deadline First (EDF)
class EarliestDeadlineFirstScheduler : public Scheduler {
public:
    EarliestDeadlineFirstScheduler() : Scheduler("Earliest Deadline First (EDF)") {}

    Job* select_task(const std::vector<Job*>& ready_queue) override {
        if (ready_queue.empty()) return nullptr;

        // Min absolute deadline
        auto it = std::min_element(ready_queue.begin(), ready_queue.end(), 
            [](const Job* a, const Job* b) {
                return a->abs_deadline < b->abs_deadline;
            });
        return *it;
    }
};

// 3. First Come First Served (FCFS)
class FirstComeFirstServedScheduler : public Scheduler {
public:
    FirstComeFirstServedScheduler() : Scheduler("First Come First Served (FCFS)") {}

    Job* select_task(const std::vector<Job*>& ready_queue) override {
        if (ready_queue.empty()) return nullptr;
        // Min release time
        auto it = std::min_element(ready_queue.begin(), ready_queue.end(), 
            [](const Job* a, const Job* b) {
                return a->current_release < b->current_release;
            });
        return *it;
    }
};

// 4. Shortest Job First (SJF)
class ShortestJobFirstScheduler : public Scheduler {
public:
    ShortestJobFirstScheduler() : Scheduler("Shortest Job First (SJF)") {}

    Job* select_task(const std::vector<Job*>& ready_queue) override {
        if (ready_queue.empty()) return nullptr;
        // Min remaining time
        auto it = std::min_element(ready_queue.begin(), ready_queue.end(), 
            [](const Job* a, const Job* b) {
                return a->remaining < b->remaining;
            });
        return *it;
    }
};

// 5. Least Slack Time (LST)
class LeastSlackTimeScheduler : public Scheduler {
public:
    LeastSlackTimeScheduler() : Scheduler("Least Slack Time (LST)") {}

    Job* select_task(const std::vector<Job*>& ready_queue) override {
        if (ready_queue.empty()) return nullptr;
        
        // Slack = abs_deadline - current_time - remaining
        auto it = std::min_element(ready_queue.begin(), ready_queue.end(), 
            [this](const Job* a, const Job* b) {
                double slack_a = a->abs_deadline - this->current_time - a->remaining;
                double slack_b = b->abs_deadline - this->current_time - b->remaining;
                return slack_a < slack_b;
            });
        return *it;
    }
};

// 6. Deadline Monotonic (DM)
class DeadlineMonotonicScheduler : public Scheduler {
public:
    DeadlineMonotonicScheduler() : Scheduler("Deadline Monotonic (DM)") {}

    Job* select_task(const std::vector<Job*>& ready_queue) override {
        if (ready_queue.empty()) return nullptr;

        // Min relative deadline
        auto it = std::min_element(ready_queue.begin(), ready_queue.end(), 
            [](const Job* a, const Job* b) {
                double da = (a->task->type == PERIODIC || a->task->type == DYNAMIC) ? a->task->deadline : 1e99;
                double db = (b->task->type == PERIODIC || b->task->type == DYNAMIC) ? b->task->deadline : 1e99;
                return da < db;
            });
        return *it;
    }
};

// --- Scheduler Factory ---
class SchedulerFactory {
public:
    static std::unique_ptr<Scheduler> create_scheduler(std::string type) {
        // Convert to upper case for comparison
        std::transform(type.begin(), type.end(), type.begin(), ::toupper);

        if (type == "RM" || type == "RATE_MONOTONIC") return std::make_unique<RateMonotonicScheduler>();
        if (type == "EDF" || type == "EARLIEST_DEADLINE_FIRST") return std::make_unique<EarliestDeadlineFirstScheduler>();
        if (type == "DM" || type == "DEADLINE_MONOTONIC") return std::make_unique<DeadlineMonotonicScheduler>();
        if (type == "FCFS" || type == "FIFO") return std::make_unique<FirstComeFirstServedScheduler>();
        if (type == "SJF" || type == "SHORTEST_JOB_FIRST") return std::make_unique<ShortestJobFirstScheduler>();
        if (type == "LST" || type == "LEAST_SLACK_TIME") return std::make_unique<LeastSlackTimeScheduler>();
        
        throw std::runtime_error("Unknown scheduler type");
    }
};
