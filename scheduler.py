#include "schedule_ali.cpp"
#include <cmath>
#include <vector>
#include <memory>
#include <algorithm>
#include <iostream>

extern "C" {
#include "rts_parser.h"
}

using namespace std;

// Helper function to convert parsed tasks into C++ Task objects
void loadTasksFromParser(ParserState* state, vector<shared_ptr<Task>>& tasks) {
    tasks.clear();
    for (int i = 0; i < state->task_count; i++) {
        ParsedTask* p_task = &state->tasks[i];
        TaskTypes type;
        
        // Map parser task type to C++ enum
        if (p_task->type == PARSED_TASK_PERIODIC) {
            type = Periodic;
        } else if (p_task->type == PARSED_TASK_DYNAMIC) {
            type = Dynamic;
        } else { // PARSED_TASK_APERIODIC
            type = Aperiodic;
        }

        tasks.push_back(make_shared<Task>(
            type,
            (double)p_task->execution_time,
            (double)p_task->period,
            (double)p_task->release_time,
            (double)p_task->deadline
        ));
    }
}

// Prints the final schedule and summary stats
void printSchedule(Scheduler* sch) {
    cout << "\n=== " << sch->getName() << " Scheduling ===" << endl;
    cout << "Time\tTask\tAction" << endl;
    cout << "----\t----\t------" << endl;

    vector<tuple<double, Job*>> logs = sch->getLogs();
    Job* prev_job = nullptr;

    for (const auto& log : logs) {
        double time = get<0>(log);
        Job* job = get<1>(log);

        if (job != prev_job) {
            if (job == nullptr) {
                cout << (int)(time + 0.5) << "\tIDLE\t-" << endl;
            } else {
                string type_str;
                if (job->getTask()->getType() == Periodic) type_str = "(P)";
                else if (job->getTask()->getType() == Dynamic) type_str = "(D)";
                else type_str = "(A)";
                
                cout << (int)(time + 0.5) << "\tT" << job->getTask()->getId() << type_str
                     << "\tExecuting (deadline: " << job->getAbsDeadline() << ")" << endl;
            }
            prev_job = job;
        }
    }

    cout << "\nSummary:" << endl;
    cout << "Completed jobs: " << sch->getFinishedJobs().size() << endl;
    cout << "Missed deadlines: " << sch->getMissedDeadlines().size() << endl;

    if (!sch->getMissedDeadlines().empty()) {
        cout << "Deadline misses for tasks: ";
        for (auto* job : sch->getMissedDeadlines()) {
            cout << "T" << job->getTask()->getId() << " at t=" << job->getAbsDeadline() << " ";
        }
        cout << endl;
    }
    cout << endl;
}

// Simulation for periodic-only schedulers (RM, EDF, LLF)
void runPeriodicSimulation(const string& name, const vector<shared_ptr<Task>>& tasks, double sim_length) {
    cout << "\n--- Running Periodic Simulation: " << name << " ---" << endl;
    
    Scheduler* sch = nullptr;
    if (name == "RM") sch = new RMScheduling();
    else if (name == "EDF") sch = new EDFScheduling();
    else if (name == "LLF") sch = new LLFScheduling();
    else {
        cerr << "Unknown periodic scheduler type." << endl;
        return;
    }

    vector<Job> all_jobs;
    all_jobs.reserve(1000);
    vector<Job*> queued_jobs;

    while (sch->getCurrentTime() < sim_length) {
        double current_time = sch->getCurrentTime();

        // Release new jobs for periodic tasks
        for (const auto& task : tasks) {
            if (task->getType() == Periodic || task->getType() == Dynamic) {
                 if (fmod(current_time, task->getP()) < 0.01 && current_time >= task->getR()) {
                    all_jobs.emplace_back(task, current_time);
                    queued_jobs.push_back(&all_jobs.back());
                }
            }
        }

        // Check for deadline misses
        for (auto it = queued_jobs.begin(); it != queued_jobs.end();) {
            if ((*it)->getAbsDeadline() <= current_time) {
                sch->addMissedDeadline(*it);
                it = queued_jobs.erase(it);
            } else {
                it++;
            }
        }
        
        // Select and execute job
        Job* now = sch->selectTask(queued_jobs);
        if (now) {
            now->execute(1.0);
            sch->addLog(now);

            if (now->isComplete()) {
                queued_jobs.erase(remove(queued_jobs.begin(), queued_jobs.end(), now), queued_jobs.end());
                sch->addFinishedJob(now);
            }
        } else {
            sch->addLog(nullptr); // Log IDLE time
        }
        sch->clockTick(1.0);
    }

    printSchedule(sch);
    delete sch;
}

// Simulation for aperiodic server-based schedulers
void runAperiodicSimulation(const vector<shared_ptr<Task>>& tasks, double sim_length, const ParsedServerConfig& server_config) {
    Scheduler* sch = nullptr;
    if (server_config.type == SERVER_POLLER) {
        sch = new PollerScheduling((double)server_config.period, (double)server_config.budget);
    } else if (server_config.type == SERVER_DEFERRABLE) {
        sch = new DeferableScheduling((double)server_config.period, (double)server_config.budget);
    } else {
        cerr << "Cannot run aperiodic simulation without a server defined." << endl;
        return;
    }
    
    cout << "\n--- Running Aperiodic Simulation: " << sch->getName() << " ---" << endl;

    vector<Job> all_jobs;
    all_jobs.reserve(1000);
    vector<Job*> queued_jobs;
    vector<bool> aperiodic_released(tasks.size(), false);

    while (sch->getCurrentTime() < sim_length) {
        double current_time = sch->getCurrentTime();

        // Release jobs
        for (size_t i = 0; i < tasks.size(); ++i) {
            const auto& task = tasks[i];
            bool should_release = false;
            if (task->getType() == Periodic || task->getType() == Dynamic) {
                if (fmod(current_time, task->getP()) < 0.01 && current_time >= task->getR()) {
                    should_release = true;
                }
            } else if (task->getType() == Aperiodic) {
                if (!aperiodic_released[i] && fabs(current_time - task->getR()) < 0.01) {
                    should_release = true;
                    aperiodic_released[i] = true;
                }
            }

            if (should_release) {
                all_jobs.emplace_back(task, current_time);
                queued_jobs.push_back(&all_jobs.back());
            }
        }

        // Check for deadline misses (only for non-aperiodic tasks)
        for (auto it = queued_jobs.begin(); it != queued_jobs.end();) {
            if ((*it)->getTask()->getType() != Aperiodic && (*it)->getAbsDeadline() <= current_time) {
                sch->addMissedDeadline(*it);
                it = queued_jobs.erase(it);
            } else {
                it++;
            }
        }

        // Replenish server budget if applicable
        sch->budgetReplenishment();

        // Select and execute job
        Job* now = sch->selectTask(queued_jobs);
        if (now) {
            sch->addLog(now);
            sch->execute_server_version(now, 1.0); // Use virtual dispatch for execution
            
            if (now->isComplete()) {
                queued_jobs.erase(remove(queued_jobs.begin(), queued_jobs.end(), now), queued_jobs.end());
                sch->addFinishedJob(now);
            }
        } else {
            sch->addLog(nullptr); // Log IDLE time
        }
        sch->clockTick(1.0);
    }
    
    printSchedule(sch);
    delete sch;
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        cerr << "Usage: " << argv[0] << " <input_file_1> [input_file_2] ..." << endl;
        return 1;
    }

    cout << "Starting RTS Simulator..." << endl;

    for (int i = 1; i < argc; ++i) {
        const string filename = argv[i];
        cout << "\n\n========== Processing file: " << filename << " ==========" << endl;

        ParserState state;
        if (parse_file(filename.c_str(), &state) < 0) {
            cerr << "Error: Failed to parse file '" << filename << "'" << endl;
            continue;
        }

        print_tasks(&state);
        print_server_config(&state);

        vector<shared_ptr<Task>> tasks;
        loadTasksFromParser(&state, tasks);

        if (state.server.type == SERVER_NONE) {
            // No server defined, run periodic schedulers
            runPeriodicSimulation("RM", tasks, 50);
            runPeriodicSimulation("EDF", tasks, 50);
            runPeriodicSimulation("LLF", tasks, 50);
        } else {
            // A server is defined, run the appropriate aperiodic simulation
            runAperiodicSimulation(tasks, 50, state.server);
        }
    }

    cout << "\n\n=== ALL TESTS COMPLETE ===" << endl;
    return 0;
}
from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from task import Task, TaskType, Job


class ScheduleEvent:
    """Represents a scheduling event"""

    def __init__(self, time: float, task: Optional[Job], event_type: str, description: str = ""):
        self.time = time
        self.task = task
        self.event_type = event_type  # 'START', 'COMPLETE', 'PREEMPT', 'DEADLINE_MISS', 'IDLE'
        self.description = description

    def __repr__(self):
        task_str = str(self.task) if self.task else "IDLE"
        return f"[{self.time:6.2f}] {self.event_type:12s} {task_str} {self.description}"


class Scheduler(ABC):
    """Abstract base class for schedulers"""

    def __init__(self, name: str):
        self.name = name
        self.current_time = 0
        self.schedule_events: List[ScheduleEvent] = []
        self.completed_tasks: List[Job] = []
        self.missed_deadlines: List[Job] = []

    @abstractmethod
    def select_task(self, ready_queue: List[Job]) -> Optional[Job]:
        """Select next task to execute from ready queue"""
        pass

    def reset(self):
        """Reset scheduler state"""
        self.current_time = 0
        self.schedule_events = []
        self.completed_tasks = []
        self.missed_deadlines = []

    def add_event(self, event: ScheduleEvent):
        """Add scheduling event"""
        self.schedule_events.append(event)

    def get_statistics(self) -> Dict:
        """Calculate scheduling statistics"""
        total_tasks = len(self.completed_tasks) + len(self.missed_deadlines)

        stats = {
            'scheduler': self.name,
            'total_tasks': total_tasks,
            'completed_tasks': len(self.completed_tasks),
            'missed_deadlines': len(self.missed_deadlines),
            'success_rate': 0 if total_tasks == 0 else len(self.completed_tasks) / total_tasks * 100,
            'total_time': self.current_time
        }

        # Calculate response times and waiting times
        if self.completed_tasks:
            response_times = [t.start_time - t.current_release for t in self.completed_tasks if t.start_time is not None]
            completion_times = [t.completion_time - t.current_release for t in self.completed_tasks if t.completion_time is not None]

            if response_times:
                stats['avg_response_time'] = sum(response_times) / len(response_times)
                stats['max_response_time'] = max(response_times)

            if completion_times:
                stats['avg_completion_time'] = sum(completion_times) / len(completion_times)

        return stats


class RateMonotonicScheduler(Scheduler):
    """Rate Monotonic (RM) Scheduler - Fixed priority based on period"""

    def __init__(self):
        super().__init__("Rate Monotonic (RM)")

    def select_task(self, ready_queue: List[Job]) -> Optional[Job]:
        """Select task with shortest period (highest priority)"""
        if not ready_queue:
            return None

        # Select job with minimum period (aperiodic tasks have infinite period)
        return min(ready_queue, key=lambda j: j.task.period if j.task.type in (TaskType.PERIODIC, TaskType.DYNAMIC) else float('inf'))


class EarliestDeadlineFirstScheduler(Scheduler):
    """Earliest Deadline First (EDF) Scheduler - Dynamic priority based on deadline"""

    def __init__(self):
        super().__init__("Earliest Deadline First (EDF)")

    def select_task(self, ready_queue: List[Job]) -> Optional[Job]:
        """Select task with earliest absolute deadline"""
        if not ready_queue:
            return None

        # Find task with minimum absolute deadline
        return min(ready_queue, key=lambda t: t.abs_deadline)


class FirstComeFirstServedScheduler(Scheduler):
    """First Come First Served (FCFS) Scheduler - Non-preemptive"""

    def __init__(self):
        super().__init__("First Come First Served (FCFS)")

    def select_task(self, ready_queue: List[Job]) -> Optional[Job]:
        """Select task with earliest release time (FIFO)"""
        if not ready_queue:
            return None

        # Find task with minimum release time
        return min(ready_queue, key=lambda t: t.current_release)


class ShortestJobFirstScheduler(Scheduler):
    """Shortest Job First (SJF) Scheduler"""

    def __init__(self):
        super().__init__("Shortest Job First (SJF)")

    def select_task(self, ready_queue: List[Job]) -> Optional[Job]:
        """Select task with shortest remaining execution time"""
        if not ready_queue:
            return None

        # Find task with minimum remaining time
        return min(ready_queue, key=lambda t: t.remaining)


class LeastSlackTimeScheduler(Scheduler):
    """Least Slack Time (LST) Scheduler"""

    def __init__(self):
        super().__init__("Least Slack Time (LST)")

    def select_task(self, ready_queue: List[Job]) -> Optional[Job]:
        """Select task with least slack time (deadline - current_time - remaining_time)"""
        if not ready_queue:
            return None

        # Find task with minimum slack
        def slack(job: Job) -> float:
            return job.abs_deadline - self.current_time - job.remaining

        return min(ready_queue, key=slack)


class DeadlineMonotonicScheduler(Scheduler):
    """Deadline Monotonic (DM) Scheduler - Fixed priority based on relative deadline"""

    def __init__(self):
        super().__init__("Deadline Monotonic (DM)")

    def select_task(self, ready_queue: List[Job]) -> Optional[Job]:
        """Select task with shortest relative deadline (highest priority)"""
        if not ready_queue:
            return None

        # Select job with minimum deadline (aperiodic tasks have infinite deadline)
        return min(ready_queue, key=lambda j: j.task.deadline if j.task.type in (TaskType.PERIODIC, TaskType.DYNAMIC) else float('inf'))


class SchedulerFactory:
    """Factory for creating scheduler instances"""

    @staticmethod
    def create_scheduler(scheduler_type: str) -> Scheduler:
        """Create scheduler by type"""
        scheduler_type = scheduler_type.upper()

        if scheduler_type in ['RM', 'RATE_MONOTONIC']:
            return RateMonotonicScheduler()
        elif scheduler_type in ['EDF', 'EARLIEST_DEADLINE_FIRST']:
            return EarliestDeadlineFirstScheduler()
        elif scheduler_type in ['DM', 'DEADLINE_MONOTONIC']:
            return DeadlineMonotonicScheduler()
        elif scheduler_type in ['FCFS', 'FIFO']:
            return FirstComeFirstServedScheduler()
        elif scheduler_type in ['SJF', 'SHORTEST_JOB_FIRST']:
            return ShortestJobFirstScheduler()
        elif scheduler_type in ['LST', 'LEAST_SLACK_TIME']:
            return LeastSlackTimeScheduler()
        else:
            raise ValueError(f"Unknown scheduler type: {scheduler_type}")

    @staticmethod
    def get_available_schedulers() -> List[str]:
        """Get list of available scheduler types"""
        return [
            'RM (Rate Monotonic)',
            'EDF (Earliest Deadline First)',
            'DM (Deadline Monotonic)',
            'FCFS (First Come First Served)',
            'SJF (Shortest Job First)',
            'LST (Least Slack Time)'
        ]
