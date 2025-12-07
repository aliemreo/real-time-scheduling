#include <iostream>
#include <vector>
#include <memory>

enum TaskTypes {Periodic, Dynamic, Aperiodic};
enum ServerTypes {None, Background, Poller, Defferable};

class Task {
private:
    static int num_tasks; 
    int id;
    TaskTypes type;
    double exec_time;
    double per;
    double rel_time;
    double deadline;
    ServerTypes server;
public:
    Task(TaskTypes t, double e, double p = 0, double r = 0, double d = 0, ServerTypes s = None) 
                                        : id(++num_tasks), type(t), exec_time(e), per(p), rel_time(r), server(s) {
                                            if(d > 0) deadline = d;
                                            else deadline = p;
                                        }

    int getId() {return id;}
    TaskTypes getType() {return type;}
    double getE() {return exec_time;}
    double getP() {return per;}
    double getD() {return deadline;}
    double getR() {return rel_time;}
    ServerTypes getServer() {return server;}

/* setters
    double getE() {return exec_time;}
    double getP() {return per;}
    double getD() {return deadline;}
    double getR() {return rel_time;}
    ServerTypes getServer() {return server;}
    */
};

int Task::num_tasks = 0;

class Job {
private:
    std::shared_ptr<Task> task; //this one is for 1-many relation, shared_ptr makes life easier
    double rem;
    bool started;
    // setted at the creation
    double abs_deadline;
    double job_release_time;
public:
    Job(std::shared_ptr<Task> t, double release_time)
            : task(t), rem(t->getE()), abs_deadline(release_time + t->getD()), job_release_time(release_time), started(false) {

            }

    std::shared_ptr<Task> getTask() {return task;}
    double getRem() {return rem;}
    double getAbsDeadline() {return abs_deadline;}
    double getJobReleaseTime () { return job_release_time;}
    bool hasStarted() { return started;}

    bool isComplete() {return rem <= 0;}

    double execute(double time) {
        if(rem > 0) {
            started = true;
            if (rem - time < 0) { 
                double tmp;
                rem = 0;
                return tmp;
            }
            else { 
                rem = rem - time;
                return time;
            }
        }
        return 0;
    }
    // return sth for deadline misses???????????
};