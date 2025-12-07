#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#define MAX_LINE_LENGTH 256
#define MAX_TASKS 100

// Task types
typedef enum {
    TASK_PERIODIC,
    TASK_DYNAMIC,
    TASK_APERIODIC
} TaskType;

// Consumption rule types
typedef enum {
    CONSUMPTION_ONLY_WHEN_EXECUTING,
    CONSUMPTION_ALWAYS,
    CONSUMPTION_NONE
} ConsumptionRule;

// Replenishment rule types
typedef enum {
    REPLENISHMENT_PERIODIC,
    REPLENISHMENT_SPORADIC,
    REPLENISHMENT_NONE
} ReplenishmentRule;

// Task structure
typedef struct {
    TaskType type;
    int release_time;   // ri
    int execution_time; // ei
    int period;         // pi
    int deadline;       // di
} Task;

// Server configuration
typedef struct {
    ConsumptionRule consumption;
    ReplenishmentRule replenishment;
    int replenishment_period;
} ServerConfig;

// Parser state
typedef struct {
    Task tasks[MAX_TASKS];
    int task_count;
    ServerConfig server;
} ParserState;

// Function prototypes
void init_parser_state(ParserState *state);
int parse_file(const char *filename, ParserState *state);
int parse_line(char *line, ParserState *state);
int parse_periodic_task(char *line, ParserState *state);
int parse_dynamic_task(char *line, ParserState *state);
int parse_aperiodic_task(char *line, ParserState *state);
int parse_consumption_rule(char *line, ParserState *state);
int parse_replenishment_rule(char *line, ParserState *state);
void trim_whitespace(char *str);
void print_tasks(ParserState *state);
void print_server_config(ParserState *state);

// Initialize parser state
void init_parser_state(ParserState *state) {
    state->task_count = 0;
    state->server.consumption = CONSUMPTION_NONE;
    state->server.replenishment = REPLENISHMENT_NONE;
    state->server.replenishment_period = 0;
}

// Trim leading and trailing whitespace
void trim_whitespace(char *str) {
    char *start = str;
    char *end;

    // Trim leading space
    while (isspace((unsigned char)*start)) start++;

    // All spaces?
    if (*start == 0) {
        *str = 0;
        return;
    }

    // Trim trailing space
    end = start + strlen(start) - 1;
    while (end > start && isspace((unsigned char)*end)) end--;

    // Write new null terminator
    *(end + 1) = 0;

    // Move trimmed string to beginning
    if (start != str) {
        memmove(str, start, strlen(start) + 1);
    }
}

// Parse periodic task: P ri ei pi di OR P ri ei pi OR P ei pi
int parse_periodic_task(char *line, ParserState *state) {
    Task task;
    task.type = TASK_PERIODIC;

    int values[4];
    int count = 0;
    char *token = strtok(line, " \t");

    // Skip 'P'
    token = strtok(NULL, " \t");

    // Read all numeric values
    while (token != NULL && count < 4) {
        values[count++] = atoi(token);
        token = strtok(NULL, " \t");
    }

    if (count == 2) {
        // Format: P ei pi
        task.release_time = 0;
        task.execution_time = values[0];
        task.period = values[1];
        task.deadline = values[1];  // Implicit deadline = period
    } else if (count == 3) {
        // Format: P ri ei pi
        task.release_time = values[0];
        task.execution_time = values[1];
        task.period = values[2];
        task.deadline = values[2];  // Implicit deadline = period
    } else if (count == 4) {
        // Format: P ri ei pi di
        task.release_time = values[0];
        task.execution_time = values[1];
        task.period = values[2];
        task.deadline = values[3];
    } else {
        fprintf(stderr, "Error: Invalid periodic task format (expected 2, 3, or 4 parameters)\n");
        return -1;
    }

    if (state->task_count >= MAX_TASKS) {
        fprintf(stderr, "Error: Maximum number of tasks exceeded\n");
        return -1;
    }

    state->tasks[state->task_count++] = task;
    return 0;
}

// Parse dynamic task: D ei pi di
int parse_dynamic_task(char *line, ParserState *state) {
    Task task;
    task.type = TASK_DYNAMIC;
    task.release_time = 0;  // Dynamic tasks typically start at 0

    int values[3];
    int count = 0;
    char *token = strtok(line, " \t");

    // Skip 'D'
    token = strtok(NULL, " \t");

    // Read all numeric values
    while (token != NULL && count < 3) {
        values[count++] = atoi(token);
        token = strtok(NULL, " \t");
    }

    if (count != 3) {
        fprintf(stderr, "Error: Invalid dynamic task format (expected 3 parameters: ei pi di)\n");
        return -1;
    }

    task.execution_time = values[0];
    task.period = values[1];
    task.deadline = values[2];

    if (state->task_count >= MAX_TASKS) {
        fprintf(stderr, "Error: Maximum number of tasks exceeded\n");
        return -1;
    }

    state->tasks[state->task_count++] = task;
    return 0;
}

// Parse aperiodic task: A ri ei
int parse_aperiodic_task(char *line, ParserState *state) {
    Task task;
    task.type = TASK_APERIODIC;
    task.period = 0;    // Aperiodic tasks have no period
    task.deadline = 0;  // No deadline for aperiodic tasks

    int values[2];
    int count = 0;
    char *token = strtok(line, " \t");

    // Skip 'A'
    token = strtok(NULL, " \t");

    // Read all numeric values
    while (token != NULL && count < 2) {
        values[count++] = atoi(token);
        token = strtok(NULL, " \t");
    }

    if (count != 2) {
        fprintf(stderr, "Error: Invalid aperiodic task format (expected 2 parameters: ri ei)\n");
        return -1;
    }

    task.release_time = values[0];
    task.execution_time = values[1];

    if (state->task_count >= MAX_TASKS) {
        fprintf(stderr, "Error: Maximum number of tasks exceeded\n");
        return -1;
    }

    state->tasks[state->task_count++] = task;
    return 0;
}

// Parse consumption rule
int parse_consumption_rule(char *line, ParserState *state) {
    char *token = strtok(line, " \t");

    // Skip "CONSUMPTION_RULE"
    token = strtok(NULL, " \t");

    if (token == NULL) {
        fprintf(stderr, "Error: Missing consumption rule value\n");
        return -1;
    }

    if (strcmp(token, "ONLY_WHEN_EXECUTING") == 0) {
        state->server.consumption = CONSUMPTION_ONLY_WHEN_EXECUTING;
    } else if (strcmp(token, "ALWAYS") == 0) {
        state->server.consumption = CONSUMPTION_ALWAYS;
    } else {
        fprintf(stderr, "Error: Unknown consumption rule: %s\n", token);
        return -1;
    }

    return 0;
}

// Parse replenishment rule
int parse_replenishment_rule(char *line, ParserState *state) {
    char *token = strtok(line, " \t");

    // Skip "REPLENISHMENT_RULE"
    token = strtok(NULL, " \t");

    if (token == NULL) {
        fprintf(stderr, "Error: Missing replenishment rule value\n");
        return -1;
    }

    if (strcmp(token, "PERIODIC") == 0) {
        state->server.replenishment = REPLENISHMENT_PERIODIC;

        // Get period value
        token = strtok(NULL, " \t");
        if (token != NULL) {
            state->server.replenishment_period = atoi(token);
        }
    } else if (strcmp(token, "SPORADIC") == 0) {
        state->server.replenishment = REPLENISHMENT_SPORADIC;
    } else {
        fprintf(stderr, "Error: Unknown replenishment rule: %s\n", token);
        return -1;
    }

    return 0;
}

// Parse a single line
int parse_line(char *line, ParserState *state) {
    trim_whitespace(line);

    // Skip empty lines
    if (strlen(line) == 0) {
        return 0;
    }

    // Skip comment lines
    if (line[0] == '#') {
        return 0;
    }

    // Make a copy for parsing (strtok modifies the string)
    char line_copy[MAX_LINE_LENGTH];
    strncpy(line_copy, line, MAX_LINE_LENGTH - 1);
    line_copy[MAX_LINE_LENGTH - 1] = '\0';

    // Determine line type
    if (line[0] == 'P') {
        return parse_periodic_task(line_copy, state);
    } else if (line[0] == 'D') {
        return parse_dynamic_task(line_copy, state);
    } else if (line[0] == 'A') {
        return parse_aperiodic_task(line_copy, state);
    } else if (strncmp(line, "CONSUMPTION_RULE", 16) == 0) {
        return parse_consumption_rule(line_copy, state);
    } else if (strncmp(line, "REPLENISHMENT_RULE", 18) == 0) {
        return parse_replenishment_rule(line_copy, state);
    } else {
        fprintf(stderr, "Warning: Unknown line format: %s\n", line);
        return 0;  // Continue parsing
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

    while (fgets(line, sizeof(line), file)) {
        line_number++;

        // Remove newline character
        size_t len = strlen(line);
        if (len > 0 && line[len - 1] == '\n') {
            line[len - 1] = '\0';
        }
        if (len > 1 && line[len - 2] == '\r') {
            line[len - 2] = '\0';
        }

        if (parse_line(line, state) < 0) {
            fprintf(stderr, "Error at line %d\n", line_number);
            fclose(file);
            return -1;
        }
    }

    fclose(file);
    return 0;
}

// Print parsed tasks
void print_tasks(ParserState *state) {
    printf("\n=== Parsed Tasks ===\n");
    printf("Total tasks: %d\n\n", state->task_count);

    for (int i = 0; i < state->task_count; i++) {
        Task *t = &state->tasks[i];
        printf("Task %d:\n", i + 1);

        switch (t->type) {
            case TASK_PERIODIC:
                printf("  Type: Periodic\n");
                printf("  Release time: %d\n", t->release_time);
                printf("  Execution time: %d\n", t->execution_time);
                printf("  Period: %d\n", t->period);
                printf("  Deadline: %d\n", t->deadline);
                break;
            case TASK_DYNAMIC:
                printf("  Type: Dynamic\n");
                printf("  Release time: %d\n", t->release_time);
                printf("  Execution time: %d\n", t->execution_time);
                printf("  Period: %d\n", t->period);
                printf("  Deadline: %d\n", t->deadline);
                break;
            case TASK_APERIODIC:
                printf("  Type: Aperiodic\n");
                printf("  Release time: %d\n", t->release_time);
                printf("  Execution time: %d\n", t->execution_time);
                break;
        }
        printf("\n");
    }
}

// Print server configuration
void print_server_config(ParserState *state) {
    printf("=== Server Configuration ===\n");

    printf("Consumption Rule: ");
    switch (state->server.consumption) {
        case CONSUMPTION_ONLY_WHEN_EXECUTING:
            printf("ONLY_WHEN_EXECUTING\n");
            break;
        case CONSUMPTION_ALWAYS:
            printf("ALWAYS\n");
            break;
        case CONSUMPTION_NONE:
            printf("Not specified\n");
            break;
    }

    printf("Replenishment Rule: ");
    switch (state->server.replenishment) {
        case REPLENISHMENT_PERIODIC:
            printf("PERIODIC (period: %d)\n", state->server.replenishment_period);
            break;
        case REPLENISHMENT_SPORADIC:
            printf("SPORADIC\n");
            break;
        case REPLENISHMENT_NONE:
            printf("Not specified\n");
            break;
    }
    printf("\n");
}

// Main function for testing
int main(int argc, char *argv[]) {
    if (argc != 2) {
        printf("Usage: %s <input_file>\n", argv[0]);
        return 1;
    }

    ParserState state;
    init_parser_state(&state);

    printf("Parsing file: %s\n", argv[1]);

    if (parse_file(argv[1], &state) < 0) {
        fprintf(stderr, "Failed to parse file\n");
        return 1;
    }

    printf("File parsed successfully!\n");

    print_tasks(&state);
    print_server_config(&state);

    return 0;
}
