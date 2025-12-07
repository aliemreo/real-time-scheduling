#include "rts_parser.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <math.h>

// Internal function prototypes
static int parse_line(char *line, ParserState *state);
static int parse_periodic_task(char *line, ParserState *state);
static int parse_dynamic_task(char *line, ParserState *state);
static int parse_aperiodic_task(char *line, ParserState *state);
static int parse_server_config(char *line, ParserState *state);
static void trim_whitespace(char *str);

// Initialize parser state
void init_parser_state(ParserState *state) {
    state->task_count = 0;
    state->server.type = SERVER_NONE;
    state->server.budget = 0;
    state->server.period = 0;
    state->server.scheduling = SCHED_NONE;
}

// Trim leading and trailing whitespace from a string
static void trim_whitespace(char *str) {
    if (!str) return;
    char *start = str;
    while (isspace((unsigned char)*start)) {
        start++;
    }

    if (*start == 0) {
        *str = 0;
        return;
    }

    char *end = start + strlen(start) - 1;
    while (end > start && isspace((unsigned char)*end)) {
        end--;
    }
    *(end + 1) = 0;

    if (str != start) {
        memmove(str, start, strlen(start) + 1);
    }
}

// Parse periodic task: P [ri] ei pi [di]
static int parse_periodic_task(char *line, ParserState *state) {
    ParsedTask task;
    task.type = PARSED_TASK_PERIODIC;

    int values[4];
    int count = 0;
    char *token = strtok(line, " 	"); // Skip 'P'
    token = strtok(NULL, " 	");

    while (token != NULL && count < 4) {
        values[count++] = atoi(token);
        token = strtok(NULL, " 	");
    }

    if (count == 2) { // P ei pi
        task.release_time = 0;
        task.execution_time = values[0];
        task.period = values[1];
        task.deadline = values[1]; // Implicit deadline
    } else if (count == 3) { // P ri ei pi
        task.release_time = values[0];
        task.execution_time = values[1];
        task.period = values[2];
        task.deadline = values[2]; // Implicit deadline
    } else if (count == 4) { // P ri ei pi di
        task.release_time = values[0];
        task.execution_time = values[1];
        task.period = values[2];
        task.deadline = values[3];
    } else {
        fprintf(stderr, "Error: Invalid periodic task format. Expected 'P [ri] ei pi [di]'.\n");
        return -1;
    }

    if (state->task_count >= MAX_TASKS) {
        fprintf(stderr, "Error: Maximum number of tasks exceeded.\n");
        return -1;
    }
    state->tasks[state->task_count++] = task;
    return 0;
}

// Parse dynamic task: D ei pi di
static int parse_dynamic_task(char *line, ParserState *state) {
    ParsedTask task;
    task.type = PARSED_TASK_DYNAMIC;

    if (sscanf(line, "D %d %d %d", &task.execution_time, &task.period, &task.deadline) != 3) {
        fprintf(stderr, "Error: Invalid dynamic task format. Expected 'D ei pi di'.\n");
        return -1;
    }
    task.release_time = 0; // Dynamic tasks start at time 0

    if (state->task_count >= MAX_TASKS) {
        fprintf(stderr, "Error: Maximum number of tasks exceeded.\n");
        return -1;
    }
    state->tasks[state->task_count++] = task;
    return 0;
}

// Parse aperiodic task: A ri ei
static int parse_aperiodic_task(char *line, ParserState *state) {
    ParsedTask task;
    task.type = PARSED_TASK_APERIODIC;
    
    if (sscanf(line, "A %d %d", &task.release_time, &task.execution_time) != 2) {
        fprintf(stderr, "Error: Invalid aperiodic task format. Expected 'A ri ei'.\n");
        return -1;
    }
    task.period = -1;
    task.deadline = 0;

    if (state->task_count >= MAX_TASKS) {
        fprintf(stderr, "Error: Maximum number of tasks exceeded.\n");
        return -1;
    }
    state->tasks[state->task_count++] = task;
    return 0;
}

// Parse server config: S es ps TYPE SCHEDULING
static int parse_server_config(char *line, ParserState *state) {
    char server_type_str[50];
    char scheduling_type_str[50];
    int budget, period;

    if (sscanf(line, "S %d %d %49s %49s", &budget, &period, server_type_str, scheduling_type_str) != 4) {
        fprintf(stderr, "Error: Invalid server format. Expected 'S es ps TYPE SCHEDULING'.\n");
        return -1;
    }

    state->server.budget = budget;
    state->server.period = period;

    if (strcmp(server_type_str, "DEFERABLE") == 0) {
        state->server.type = SERVER_DEFERRABLE;
    } else if (strcmp(server_type_str, "POLLER") == 0) {
        state->server.type = SERVER_POLLER;
    } else if (strcmp(server_type_str, "BACKGROUND") == 0) {
        state->server.type = SERVER_BACKGROUND;
    } else {
        fprintf(stderr, "Error: Unknown server type '%s'. Use 'POLLER' or 'DEFERABLE' or 'BACKGROUND'.\n", server_type_str);
        return -1;
    }

    if (strcmp(scheduling_type_str, "RM") == 0) {
        state->server.scheduling = SCHED_RM;
    } else if (strcmp(scheduling_type_str, "EDF") == 0) {
        state->server.scheduling = SCHED_EDF;
    } else {
        fprintf(stderr, "Error: Unknown scheduling type '%s'. Use 'RM' or 'EDF'.\n", scheduling_type_str);
        return -1;
    }
    return 0;
}


// Main line parsing function
static int parse_line(char *line, ParserState *state) {
    trim_whitespace(line);
    if (strlen(line) == 0 || line[0] == '#') {
        return 0; // Skip empty lines and comments
    }

    switch (line[0]) {
        case 'P': return parse_periodic_task(line, state);
        case 'D': return parse_dynamic_task(line, state);
        case 'A': return parse_aperiodic_task(line, state);
        case 'S': return parse_server_config(line, state);
        default:
            fprintf(stderr, "Warning: Unknown line format, ignoring: %s\n", line);
            return 0;
    }
}

// Parse file
int parse_file(const char *filename, ParserState *state) {
    FILE *file = fopen(filename, "r");
    if (file == NULL) {
        fprintf(stderr, "Error: Cannot open file '%s'\n", filename);
        return -1;
    }

    char line[MAX_LINE_LENGTH];
    int line_number = 0;
    init_parser_state(state); // Ensure state is clean before parsing

    while (fgets(line, sizeof(line), file)) {
        line_number++;
        if (parse_line(line, state) < 0) {
            fprintf(stderr, "Error parsing file '%s' at line %d.\n", filename, line_number);
            fclose(file);
            return -1;
        }
    }

    fclose(file);
    return 0;
}

// --- Utility printing functions ---

const char* task_type_to_string(ParsedTaskType type) {
    switch (type) {
        case PARSED_TASK_PERIODIC: return "Periodic";
        case PARSED_TASK_DYNAMIC: return "Dynamic";
        case PARSED_TASK_APERIODIC: return "Aperiodic";
        default: return "Unknown";
    }
}

const char* server_type_to_string(ParsedServerType type) {
    switch (type) {
        case SERVER_POLLER: return "POLLER";
        case SERVER_DEFERRABLE: return "DEFERRABLE";
        case SERVER_BACKGROUND: return "BACKGROUND";
        default: return "NONE";
    }
}

const char* scheduling_type_to_string(ParsedSchedulingType type) {
    switch (type) {
        case SCHED_RM: return "RM";
        case SCHED_EDF: return "EDF";
        default: return "NONE";
    }
}

void print_tasks(ParserState *state) {
    printf("\n=== Parsed Tasks ===\n");
    printf("Total tasks: %d\n\n", state->task_count);
    for (int i = 0; i < state->task_count; i++) {
        ParsedTask *t = &state->tasks[i];
        printf("Task %d (%s):\n", i + 1, task_type_to_string(t->type));
        printf("  Release: %d, Exec: %d, Period: %d, Deadline: %f\n\n",
               t->release_time, t->execution_time, (t->type == PARSED_TASK_APERIODIC) ? state->server.period :  t->period, (t->type == PARSED_TASK_APERIODIC) ? INFINITY: t->deadline);
    }
}

void print_server_config(ParserState *state) {
    if (state->server.type != SERVER_NONE) {
        printf("=== Server Configuration ===\n");
        printf("  Type: %s\n", server_type_to_string(state->server.type));
        printf("  Budget: %d\n", state->server.budget);
        printf("  Period: %d\n", state->server.period);
        printf("  Scheduling: %s\n", scheduling_type_to_string(state->server.scheduling));
        printf("\n");
    }
}