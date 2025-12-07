#include "rts_parser.h"
#include <stdio.h>

int main(int argc, char *argv[]) {
    if (argc != 2) {
        printf("Usage: %s <input_file>\n", argv[0]);
        printf("\nExample input file formats:\n");
        printf("  # Comment line\n");
        printf("  P ri ei pi di    - Periodic task with all parameters\n");
        printf("  P ri ei pi       - Periodic task (deadline = period)\n");
        printf("  P ei pi          - Periodic task (release=0, deadline=period)\n");
        printf("  D ei pi di       - Dynamic task\n");
        printf("  A ri ei          - Aperiodic task\n");
        printf("  CONSUMPTION_RULE ONLY_WHEN_EXECUTING\n");
        printf("  REPLENISHMENT_RULE PERIODIC <period>\n");
        return 1;
    }

    ParserState state;
    init_parser_state(&state);

    printf("========================================\n");
    printf("Real-Time Scheduling Task File Parser\n");
    printf("========================================\n\n");
    printf("Parsing file: %s\n", argv[1]);

    if (parse_file(argv[1], &state) < 0) {
        fprintf(stderr, "\nFailed to parse file!\n");
        return 1;
    }

    printf("\nFile parsed successfully!\n");

    print_tasks(&state);
    print_server_config(&state);

    printf("========================================\n");
    printf("Parsing complete.\n");
    printf("========================================\n");

    return 0;
}
