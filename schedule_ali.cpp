#include "task_ali.cpp"
#include <string>
#include <cmath>

extern "C" {
#include "rts_parser.h"
}

using namespace std;

class Scheduler {
private:
    string name;
    double curr_time;
    // i found a way to push multiple types using tuples
    vector<tuple<double, Job*>> logs;
    vector<Job*> finished_jobs;
    vector<Job*> missed_deadlines;

public:

    Scheduler(string n) : name(n), curr_time(0) {}

    void clockTick(double t) {
        curr_time = curr_time + t;
    }
    double getCurrentTime() {
        return curr_time;
    }
    void addLog(Job* job) {
        logs.push_back({curr_time, job});
    }
    void addFinishedJob(Job* job) {
        finished_jobs.push_back(job);
    }
    void addMissedDeadline(Job* job) {
        missed_deadlines.push_back(job);
    }
    //delete????????
    // Getters for printing results
    vector<tuple<double, Job*>> getLogs() { return logs; }
    vector<Job*> getFinishedJobs() { return finished_jobs; }
    vector<Job*> getMissedDeadlines() { return missed_deadlines; }
    string getName() { return name; }

    // to be able to access to the child's function from pointer of this one
    virtual Job* selectTask(vector<Job*> queue) = 0;

    // Default implementations for non-server schedulers (RM, EDF, LLF)
    virtual double budgetReplenishment() { return 0; }
    virtual double budgetConsumption(double exec) { return 0; }
    virtual void execute_server_version(Job* job, double t) {
        if(job) job->execute(t);
    }
    virtual double getReplenishmentPeriod() { return 0; }
};

class RMScheduling : public Scheduler {
private:
public:
    RMScheduling() : Scheduler("Rate Monotonic") {}
    // dynamic?????
    Job* selectTask(vector<Job*> queue) {
        if (queue.empty()) return NULL;

        //select the highest priority
        Job* highest = queue.front();
        for(int i = 1; i < queue.size(); i++) {
            if(queue[i]->getTask()->getP() < highest->getTask()->getP()) highest = queue[i];
        }

        return highest;
    } 
};

class DMScheduling : public Scheduler {
    private:
    public:
        DMScheduling() : Scheduler("Deadline Monotonic") {}
        // dynamic?????
        Job* selectTask(vector<Job*> queue) {
            if (queue.empty()) return NULL;
    
            //select the highest priority
            Job* highest = queue.front();
            for(int i = 1; i < queue.size(); i++) {
                if(queue[i]->getTask()->getD() < highest->getTask()->getD()) highest = queue[i];
            }
    
            return highest;
        } 
    };

class EDFScheduling : public Scheduler {

public:
    EDFScheduling() : Scheduler("Earliest Deadline First") {}
 
    Job* selectTask(vector<Job*> queue) {
        if (queue.empty()) return NULL;

        //select the highest priority
        Job* highest = queue.front();
        for(int i = 1; i < queue.size(); i++) {
            if(queue[i]->getAbsDeadline() < highest->getAbsDeadline()) highest = queue[i];
        }

        return highest;
    } 
};

class LLFScheduling : public Scheduler {

public:
    LLFScheduling() : Scheduler("Least Laxity First") {}
 
    Job* selectTask(vector<Job*> queue) {
        if (queue.empty()) return NULL;

        //select the highest priority (lowest laxity)
        // Laxity = deadline - currentTime - remainingExecution
        Job* highest = queue.front();
        double curr = getCurrentTime();
        for(int i = 1; i < queue.size(); i++) {
            double laxity_i = queue[i]->getAbsDeadline() - curr - queue[i]->getRem();
            double laxity_highest = highest->getAbsDeadline() - curr - highest->getRem();
            if(laxity_i < laxity_highest) highest = queue[i];
        }

        return highest;
    } 
};

class BackgroundScheduling : public Scheduler {
private:
    ParsedSchedulingType sched_type;

    // Helper: compare two jobs based on scheduling type (returns true if j1 has higher priority)
    bool hasHigherPriority(Job* j1, Job* j2) {
        if (sched_type == SCHED_RM) {
            return j1->getTask()->getP() < j2->getTask()->getP();
        } else { // SCHED_EDF
            return j1->getAbsDeadline() < j2->getAbsDeadline();
        }
    }

public:
    BackgroundScheduling(ParsedSchedulingType st = SCHED_RM)
        : Scheduler("Background Scheduling"), sched_type(st) {}

    Job* selectTask(vector<Job*> q) {
        Job* highest = NULL;
        vector<Job*> periodic_queue;
        vector<Job*> aperiodic_queue;

        // Separate periodic and aperiodic tasks
        for(int k = 0; k < q.size(); k++) {
            if(q[k]->getTask()->getType() == Periodic || q[k]->getTask()->getType() == Dynamic) {
                periodic_queue.push_back(q[k]);
            }
            else {
                aperiodic_queue.push_back(q[k]);
            }
        }

        // Background scheduling: periodic tasks have absolute priority
        if (!periodic_queue.empty()) {
            // Select highest priority periodic task using base scheduler (RM or EDF)
            highest = periodic_queue.front();
            for(int i = 1; i < periodic_queue.size(); i++) {
                if(hasHigherPriority(periodic_queue[i], highest)) {
                    highest = periodic_queue[i];
                }
            }
        }
        else if (!aperiodic_queue.empty()) {
            // Only run aperiodic tasks when NO periodic tasks are waiting
            // Use FCFS: select the first aperiodic task in the queue
            highest = aperiodic_queue.front();
        }

        return highest;
    }
};

class PollerScheduling : public Scheduler {
private:
    const double budget;
    double rem_budget = 0;
    double rep_period;
    ParsedSchedulingType sched_type;

    // Helper: compare two jobs based on scheduling type (returns true if j1 has higher priority)
    bool hasHigherPriority(Job* j1, Job* j2) {
        if (sched_type == SCHED_RM) {
            return j1->getTask()->getP() < j2->getTask()->getP();
        } else { // SCHED_EDF
            return j1->getAbsDeadline() < j2->getAbsDeadline();
        }
    }

public:
    PollerScheduling(double r, double b, ParsedSchedulingType st = SCHED_RM)
        : Scheduler("Poller Scheduling"), rep_period(r), budget(b), sched_type(st) {}
 
    Job* selectTask(vector<Job*> q) {
        Job* highest = NULL;
        vector<Job*> queue;
        vector<Job*> aper_queue;
        for(int k = 0; k < q.size(); k++) {
            if(q[k]->getTask()->getType() == Periodic) {
                queue.push_back(q[k]);
            }
            else {
                aper_queue.push_back(q[k]);
            }
        }

        if (rem_budget > 0) {
            // if there is no waiting periodic job then select the aperiodic job that has the most privilege
            if(!aper_queue.empty()) {
                // FCFS: serve aperiodic tasks in arrival order
                highest = aper_queue.front();

                // Compare periodic tasks against server using configured scheduling
                if(queue.size() != 0) {
                    // Find highest priority periodic
                    Job* highest_periodic = queue.front();
                    for(int i = 1; i < queue.size(); i++) {
                        if(hasHigherPriority(queue[i], highest_periodic)) {
                            highest_periodic = queue[i];
                        }
                    }
                    // Check if periodic has priority over server (compare with replenishment period)
                    bool periodic_preempts = false;
                    if (sched_type == SCHED_RM) {
                        periodic_preempts = (highest_periodic->getTask()->getP() < rep_period);
                    } else { // SCHED_EDF
                        periodic_preempts = (highest_periodic->getAbsDeadline() < getCurrentTime() + rep_period);
                    }

                    if(periodic_preempts) {
                        highest = highest_periodic;
                        rem_budget = 0;  // Discard budget when periodic preempts
                    }
                }
            }
            else if(!queue.empty()) {
                // Only periodic tasks, with budget available
                rem_budget = 0;  // Polling Server: discard unused budget
                highest = queue.front();
                // Select periodic task based on scheduling type
                for(int i = 1; i < queue.size(); i++) {
                    if(hasHigherPriority(queue[i], highest))
                        highest = queue[i];
                }
            }
        }
        else {
        //select the highest priority based on scheduling type
            if(queue.size() != 0) {
                highest = queue.front();
                for(int i = 1; i < queue.size(); i++) {
                    if(hasHigherPriority(queue[i], highest)) highest = queue[i];
                }
            }
        }
        return highest;
    }

    double budgetReplenishment() {
        if(std::fmod(getCurrentTime(), rep_period) < 0.01) {
            rem_budget = budget;
        }
        return rem_budget;
    }

    double budgetConsumption(double exec) {
        double consumed = 0;
        if(rem_budget > 0) {
            if(rem_budget > exec) {
                consumed = exec;
                rem_budget = 0;
            }
            else {
                consumed = rem_budget;
                rem_budget = 0;
            }
        }
        return consumed;
    }

    void execute_server_version(Job* job, double t) {
        if(job->getTask()->getType() == Aperiodic) {
            double consume = budgetConsumption(t);
            job->execute(consume);
        }
        else {
            job->execute(t);
        }
    }

    double getReplenishmentPeriod() { return rep_period; }
};


class DeferableScheduling : public Scheduler {
private:
    const double budget;
    double rem_budget = 0;
    const double rep_period;
    ParsedSchedulingType sched_type;

    // Helper: compare two jobs based on scheduling type (returns true if j1 has higher priority)
    bool hasHigherPriority(Job* j1, Job* j2) {
        if (sched_type == SCHED_RM) {
            return j1->getTask()->getP() < j2->getTask()->getP();
        } else { // SCHED_EDF
            return j1->getAbsDeadline() < j2->getAbsDeadline();
        }
    }

public:
    DeferableScheduling(double r, double b, ParsedSchedulingType st = SCHED_RM)
        : Scheduler("Deferable Scheduling"), rep_period(r), budget(b), sched_type(st) {}
 
    Job* selectTask(vector<Job*> q) {
        Job* highest = NULL;
        vector<Job*> queue;
        vector<Job*> aper_queue;
        for(int k = 0; k < q.size(); k++) {
            if(q[k]->getTask()->getType() == Periodic) {
                queue.push_back(q[k]);
            }
            else {
                aper_queue.push_back(q[k]);
            }
        }

        if (rem_budget > 0) {
            // if there is no waiting periodic job then select the aperiodic job that has the most privilege
            if(!aper_queue.empty()) {
                // FCFS: serve aperiodic tasks in arrival order
                highest = aper_queue.front();

                // Compare periodic tasks against server using configured scheduling
                if(queue.size() != 0) {
                    // Find highest priority periodic
                    Job* highest_periodic = queue.front();
                    for(int i = 1; i < queue.size(); i++) {
                        if(hasHigherPriority(queue[i], highest_periodic)) {
                            highest_periodic = queue[i];
                        }
                    }
                    // Check if periodic has priority over server (compare with replenishment period)
                    bool periodic_preempts = false;
                    if (sched_type == SCHED_RM) {
                        periodic_preempts = (highest_periodic->getTask()->getP() < rep_period);
                    } else { // SCHED_EDF
                        periodic_preempts = (highest_periodic->getAbsDeadline() < getCurrentTime() + rep_period);
                    }

                    if(periodic_preempts) {
                        highest = highest_periodic;
                    }
                }
            }
            else if(!queue.empty()) {
                // Only periodic tasks, with budget available
                // Deferrable server preserves budget when serving periodic tasks
                highest = queue.front();
                // Select periodic task based on scheduling type
                for(int i = 1; i < queue.size(); i++) {
                    if(hasHigherPriority(queue[i], highest))
                        highest = queue[i];
                }
                // Don't discard budget - Deferrable preserves it until replenishment
            }
        }
        else {
        //select the highest priority based on scheduling type
            if(queue.size() != 0) {
                highest = queue.front();
                for(int i = 1; i < queue.size(); i++) {
                    if(hasHigherPriority(queue[i], highest)) highest = queue[i];
                }
            }
        }
        return highest;
    }

    double budgetReplenishment() {
        if(std::fmod(getCurrentTime(), rep_period) < 0.01) {
            rem_budget = budget;
        }
        return rem_budget;
    }

    double budgetConsumption(double exec) {
        double consumed = 0;
        if(rem_budget > 0) {
            if(rem_budget > exec) {
                consumed = exec;
                rem_budget = rem_budget - exec;
            }
            else {
                consumed = rem_budget;
                rem_budget = 0;
            }
        }
        return consumed;
    }

    void execute_server_version(Job* job, double t) {
        if(job->getTask()->getType() == Aperiodic) {
            double consume = budgetConsumption(t);
            job->execute(consume);
        }
        else {
            job->execute(t);
        }
    }

    double getReplenishmentPeriod() { return rep_period; }

};