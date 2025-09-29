#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <inttypes.h>
#include <fcntl.h>
#include <unistd.h>

#include "superSnake_v2.h"

int main() {
    const char *fifo_py_to_c = "py_to_c.fifo";
    const char *fifo_c_to_py = "c_to_py.fifo";

    int fd_in = open(fifo_py_to_c, O_RDONLY);
    if (fd_in < 0) { perror("open read fifo"); exit(1); }

    int fd_out = open(fifo_c_to_py, O_WRONLY);
    if (fd_out < 0) { perror("open write fifo"); exit(1); }

    size_t float_matrix_size = ROWS * COLS * sizeof(float);
    size_t bufsize = float_matrix_size + 3 * sizeof(int32_t);

    void *buffer = malloc(bufsize);
    if (!buffer) { perror("malloc"); exit(1); }
    
    // interpret matrix
    float *matrix_f = (float *)buffer;

    struct Coord read_apple_coord;

    int read_current_score;

    struct GameState last_state;
    flash_initial_state(&last_state);

    double logic_blue_ratios[ROWS][COLS];

    struct Coord last_head_coord;

    MaxHeap *body_candidates;

    unsigned int detected_move;

    while (1){

        ssize_t n = read(fd_in, buffer, bufsize);
        if (n != bufsize) {
            fprintf(stderr, "Expected %zu bytes, got %zd\n", bufsize, n);
            free(buffer);
            exit(1);
        }

        // copy into double matrix
        double read_blue_ratios[ROWS][COLS];
        for (int r = 0; r < ROWS; r++) {
            for (int c = 0; c < COLS; c++) {
                read_blue_ratios[r][c] = (double)matrix_f[r * COLS + c];
            }
        }

        // interpret trailing ints
        int32_t *ints = (int32_t *)((char*)buffer + float_matrix_size);

        read_apple_coord.row = ints[0];
        read_apple_coord.col = ints[1];

        read_current_score = ints[2];

        //printf("Metadata: %d %d %d\n", ints[0], ints[1], ints[2]);
        //printf("apple_coord: (%d, %d) score: %d.\n", read_apple_coord.row, read_apple_coord.col, read_current_score);

        // print full matrix
        last_head_coord = build_logic_blue_ratios(&last_state, logic_blue_ratios);

        //printf("Last head %d, %d .\n", last_head_coord.row, last_head_coord.col);

        body_candidates = mul_ratio_matrices(read_blue_ratios, logic_blue_ratios, logic_blue_ratios);
       /* 
        printf("Matrix (double precision):\n");
        for (int r = 0; r < ROWS; r++) {
            for (int c = 0; c < COLS; c++) {
                printf("%8.5f ", logic_blue_ratios[r][c]);
            }
            printf("\n");
        }
        */

        detected_move = determine_move(&last_state, body_candidates, &last_head_coord);
        //printf("Detected  move 0x%02X.\n", detected_move);
        if (detected_move){
            calculate_next_state_in_place(detected_move, &last_state);
            last_state.score = read_current_score;
            last_state.apple_coord.row = read_apple_coord.row;
            last_state.apple_coord.col = read_apple_coord.col;
            if (read_apple_coord.row != -1){
                last_state.board[read_apple_coord.row][read_apple_coord.col] = APPLE;
            }

            print_game_state(&last_state);
        }

        // send back test int
        int32_t response = detected_move;
        write(fd_out, &response, sizeof(response));
    }

    free(buffer);
    close(fd_in);
    close(fd_out);
    return 0;
}
