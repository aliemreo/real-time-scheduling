#include "schedule_ali.cpp"
#include <cmath>
#include <vector>
#include <memory>
#include <algorithm>
#include <iostream>
#include <iomanip>

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
                
                cout << time << "\tT" << job->getTask()->getId() << type_str
                    << "\tExecuting (deadline: ";

                if (job->getTask()->getType() == Aperiodic) {
                    cout << "N/A";
                    
                } else {
                    cout << std::fixed << std::setprecision(2) 
                        << job->getAbsDeadline()
                        << std::defaultfloat;    // reset formatting
                }

                cout << ")" << endl;

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
    else if (name == "DM") sch = new DMScheduling();
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
        sch = new PollerScheduling((double)server_config.period, (double)server_config.budget, server_config.scheduling);
    } else if (server_config.type == SERVER_DEFERRABLE) {
        sch = new DeferableScheduling((double)server_config.period, (double)server_config.budget, server_config.scheduling);
    } 
    else if (server_config.type == SERVER_BACKGROUND) {
        sch = new DeferableScheduling((double)server_config.period, (double)server_config.budget, server_config.scheduling);
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
            runPeriodicSimulation("DM", tasks, 50);
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
