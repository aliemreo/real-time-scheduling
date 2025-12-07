#include <iostream>
#include <vector>
#include <memory>
#include <algorithm>

// --- Enums ---
enum TaskType { PERIODIC, DYNAMIC, APERIODIC };
enum ServerType { NONE, BACKGROUND, POLLER, DEFERRABLE };

// --- Task Class ---
class Task {
private:
    static int _counter;
    int id;
    TaskType type;
    double execution_time;
    double period;
    double deadline;
    double release_time;
    ServerType server;

public:
    // Constructor handles all types via default arguments
    Task(TaskType t, double exec, double p = 0, double d = 0, double rel = 0, ServerType s = NONE)
        : id(++_counter), type(t), execution_time(exec), period(p),
          deadline(d > 0 ? d : p), release_time(rel), server(s) {}

    // Getters
    int getId() const { return id; }
    TaskType getType() const { return type; }
    double getExecutionTime() const { return execution_time; }
    double getPeriod() const { return period; }
    double getDeadline() const { return deadline; }
    double getReleaseTime() const { return release_time; }
    ServerType getServer() const { return server; }

    // Setters
    void setExecutionTime(double exec) { execution_time = exec; }
    void setPeriod(double p) { period = p; }
    void setDeadline(double d) { deadline = d; }
    void setReleaseTime(double rel) { release_time = rel; }
    void setServer(ServerType s) { server = s; }
};

int Task::_counter = 0;

// --- Job / Instance Class ---
class Job {
private:
    std::shared_ptr<Task> task; // Reference to the definition
    double remaining;
    double abs_deadline;
    double current_release;
    bool started;

public:
    Job(std::shared_ptr<Task> t, double rel_time)
        : task(t), remaining(t->getExecutionTime()),
          abs_deadline(rel_time + t->getDeadline()), current_release(rel_time), started(false) {}

    // Getters
    std::shared_ptr<Task> getTask() const { return task; }
    double getRemaining() const { return remaining; }
    double getAbsDeadline() const { return abs_deadline; }
    double getCurrentRelease() const { return current_release; }
    bool hasStarted() const { return started; }

    // Status check
    bool is_complete() const { return remaining <= 1e-9; }

    // Execute job
    void execute(double duration) {
        started = true;
        remaining = std::max(0.0, remaining - duration);
    }
};