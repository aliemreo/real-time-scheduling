#ifndef RTS_PARSER_H
#define RTS_PARSER_H

// This block allows the header to be used in both C and C++ code
#ifdef __cplusplus
extern "C" {
#endif

#define MAX_TASKS 50
#define MAX_LINE_LENGTH 256

// Represents the type of a parsed task
typedef enum {
    PARSED_TASK_PERIODIC,
    PARSED_TASK_DYNAMIC,
    PARSED_TASK_APERIODIC
} ParsedTaskType;

// Represents a single task parsed from the input file
typedef struct {
    ParsedTaskType type;
    int release_time;
    int execution_time;
    int period;
    int deadline;
} ParsedTask;

// Represents the type of server parsed from the file
typedef enum {
    SERVER_NONE,
    SERVER_POLLER,
    SERVER_DEFERRABLE,
    SERVER_BACKGROUND
} ParsedServerType;

// Represents the scheduling algorithm type
typedef enum {
    SCHED_NONE,
    SCHED_RM,
    SCHED_EDF
} ParsedSchedulingType;

// Holds the configuration for the aperiodic server
typedef struct {
    ParsedServerType type;
    int budget;
    int period;
    ParsedSchedulingType scheduling;
} ParsedServerConfig;

// Holds the entire state of the parser after reading a file
typedef struct {
    ParsedTask tasks[MAX_TASKS];
    int task_count;
    ParsedServerConfig server;
} ParserState;

// --- Function Prototypes ---

// Initializes a ParserState struct to default values
void init_parser_state(ParserState *state);

// Parses a task file and populates the ParserState struct
int parse_file(const char *filename, ParserState *state);

// Utility functions to print the parsed data
void print_tasks(ParserState *state);
void print_server_config(ParserState *state);


#ifdef __cplusplus
}
#endif

#endif // RTS_PARSER_H
