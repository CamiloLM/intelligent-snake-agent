#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <unistd.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <string.h>
#include <errno.h>
#include <time.h>

#define ROWS 15
#define COLS 17
/*==========================================================================  
 *  Game state structure and tools 
 *  ========================================================================*/

enum Direction {
    DIR_NORTH = 1 << 3,  // 0x08
    DIR_SOUTH = 1 << 2,  // 0x04
    DIR_EAST  = 1 << 1,  // 0x02
    DIR_WEST  = 1 << 0   // 0x01
};

enum Cell {
    EMPTY = 0,
    SNAKE = 1,
    HEAD  = 2,
    APPLE = 3
};

struct Coord {
    int row;
    int col;
};

struct Node {
    struct Coord pos;
    struct Node *next;
};

struct GameState {
    unsigned int next_move;  

    int score;

    struct Coord apple_coord;

    int board[15][17];   // fixed-size, avoids malloc complexity

    struct Node *snake_body_rear;  // head of queue rear of snake
    struct Node *snake_body_front;  // tail of queue front of snake
};

void print_next_move(const struct GameState *state){
    printf("bitmask: 0x%02x\n", state->next_move);
    printf("Moves: ");
    if (state->next_move & DIR_NORTH) printf("NORTH ");
    if (state->next_move & DIR_SOUTH) printf("SOUTH ");
    if (state->next_move & DIR_EAST)  printf("EAST ");
    if (state->next_move & DIR_WEST)  printf("WEST ");
    printf("\n");
}

void print_game_state(const struct GameState *state) {
    if (!state) {
        printf("GameState is NULL\n");
        return;
    }
    print_next_move(state);

    printf("Score: %d\n", state->score);

    printf("apple_coord: (%d, %d)\n", state->apple_coord.row, state->apple_coord.col);

    printf("Board (15x17):\n");
    for (int r = 0; r < 15; r++) {
        for (int c = 0; c < 17; c++) {
            int val = state->board[r][c];
            char symbol = '.';
            switch (val) {
                case EMPTY: symbol = '.'; break;
                case SNAKE: symbol = 'S'; break;
                case HEAD:  symbol = 'H'; break;
                case APPLE: symbol = 'A'; break;
            }
            printf("%c ", symbol);
        }
        printf("\n");
    }

    printf("Snake body: queue head (snake rear) -> queue tail (snake front):\n");
    struct Node *cur = state->snake_body_rear;
    int i = 0;
    while (cur) {
        printf("  [%d] (%d, %d)\n", i, cur->pos.row, cur->pos.col);
        cur = cur->next;
        i++;
    }
    if (i == 0) {
        printf("  (empty)\n");
    }

    printf("---- END OF STATE ----\n");
}

void free_state_queue(struct GameState *state){
    struct Node *current = state->snake_body_rear;
    while (current) {
        struct Node *next = current->next;
        free(current);
        current = next;
    }
    state->snake_body_rear = state->snake_body_front = NULL;
}

void flash_initial_state(struct GameState *state){

    state->next_move = DIR_EAST;

    state->score = 0;

    state->apple_coord.row = 7;
    state->apple_coord.col = 12;

    const int rows = 15, cols = 17;
    for (int r = 0; r < rows; ++r) {
        for (int c = 0; c < cols; ++c) {
            state->board[r][c] = EMPTY;
        }
    }

    state->board[7][1] = SNAKE;
    state->board[7][2] = SNAKE;
    state->board[7][3] = SNAKE;
    state->board[7][4] = HEAD;
    state->board[7][12] = APPLE;

    state->snake_body_rear = NULL;
    state->snake_body_front = NULL;

    //                  snake length       rear ... front
    int snake_body_rows[4] = {7, 7, 7, 7};
    int snake_body_cols[4] = {1, 2, 3, 4};

    for (int i = 0; i < 4; ++i){

        struct Node *new_node = malloc(sizeof(struct Node));
        if (!new_node) {
            fprintf(stderr, "malloc failed for snake node\n");
            return; // caller must handle partial snake if this happens
        }

        new_node->pos.row = snake_body_rows[i];
        new_node->pos.col = snake_body_cols[i];
        new_node->next = NULL;

        if (state->snake_body_front) {
            state->snake_body_front->next = new_node;
        } else {
            state->snake_body_rear = new_node; // first node
        }
        state->snake_body_front = new_node;
    }
}

/*==========================================================================  
 *  A useful heap implementation 
 *  ========================================================================*/

typedef struct {
    double key;
    struct Coord coord;
} HeapNode;

typedef struct {
    HeapNode *nodes;
    int size;
    int capacity;
} MaxHeap;

MaxHeap *heap_create(int capacity) {
    MaxHeap *h = malloc(sizeof(MaxHeap));
    h->nodes = malloc(capacity * sizeof(HeapNode));
    h->size = 0;
    h->capacity = capacity;
    return h;
}

void heap_swap(HeapNode *a, HeapNode *b) {
    HeapNode tmp = *a;
    *a = *b;
    *b = tmp;
}

void heap_push(MaxHeap *h, double value, int row, int col) {
    if (h->size >= h->capacity) {
        h->capacity *= 2;
        h->nodes = realloc(h->nodes, h->capacity * sizeof(HeapNode));
    }
    int i = h->size++;
    h->nodes[i].key = value;
    h->nodes[i].coord.row = row;
    h->nodes[i].coord.col = col;

    // bubble up
    while (i > 0) {
        int parent = (i - 1) / 2;
        if (h->nodes[parent].key >= h->nodes[i].key) break;
        heap_swap(&h->nodes[parent], &h->nodes[i]);
        i = parent;
    }
}

HeapNode heap_pop(MaxHeap *h) {
    if (h->size == 0) {
        fprintf(stderr, "Heap underflow\n");
        exit(1);
    }
    HeapNode root = h->nodes[0];
    h->nodes[0] = h->nodes[--h->size];

    // bubble down
    int i = 0;
    while (1) {
        int left = 2 * i + 1, right = 2 * i + 2, largest = i;
        if (left < h->size && h->nodes[left].key > h->nodes[largest].key)
            largest = left;
        if (right < h->size && h->nodes[right].key > h->nodes[largest].key)
            largest = right;
        if (largest == i) break;
        heap_swap(&h->nodes[i], &h->nodes[largest]);
        i = largest;
    }
    return root;
}

void heap_free(MaxHeap *h) {
    free(h->nodes);
    free(h);
}
/*==========================================================================  
 *  Movement functions 
 *  ========================================================================*/
struct Coord calculate_north_neighbor(struct Coord *coord){
    struct Coord north_neighbor;
    north_neighbor.row = coord->row -1;
    north_neighbor.col = coord->col;
    return north_neighbor;
}

struct Coord calculate_south_neighbor(struct Coord *coord){
    struct Coord south_neighbor;
    south_neighbor.row = coord->row +1;
    south_neighbor.col = coord->col;
    return south_neighbor;
}

struct Coord calculate_east_neighbor(struct Coord *coord){
    struct Coord east_neighbor;
    east_neighbor.row = coord->row;
    east_neighbor.col = coord->col+1;
    return east_neighbor;
}

struct Coord calculate_west_neighbor(struct Coord *coord){
    struct Coord west_neighbor;
    west_neighbor.row = coord->row;
    west_neighbor.col = coord->col-1;
    return west_neighbor;
}

int coord_in_board(struct Coord *coord){
    return coord->row >= 0 || coord->row < 15\
    || coord->col >= 0 || coord->col < 17;
}

int coords_are_equal(struct Coord *coord_a, struct Coord *coord_b){
    return (coord_a->row == coord_b->row) && (coord_a->col == coord_b->col);
}

int val_is_empty_or_apple(int val){
    return val == 0 || val == 3;
}

unsigned int calculate_possible_moves(struct GameState *state){
    struct Coord snake_rear = state->snake_body_rear->pos;
    struct Coord next_coord;
    int next_coord_val = 0;
    unsigned int next_possible_moves = 0;

    next_coord = calculate_north_neighbor(&(state->snake_body_front->pos));
    if (coord_in_board(&next_coord)){
        next_coord_val = state->board[next_coord.row][next_coord.col];
        if (val_is_empty_or_apple(next_coord_val)\
        || coords_are_equal(&snake_rear, &next_coord)){
            next_possible_moves = next_possible_moves | DIR_NORTH;
        }
    }

    next_coord = calculate_south_neighbor(&(state->snake_body_front->pos));
    if (coord_in_board(&next_coord)){
        next_coord_val = state->board[next_coord.row][next_coord.col];
        if (val_is_empty_or_apple(next_coord_val)\
        || coords_are_equal(&snake_rear, &next_coord)){
            next_possible_moves = next_possible_moves | DIR_SOUTH;
        }
    }

    next_coord = calculate_east_neighbor(&(state->snake_body_front->pos));
    if (coord_in_board(&next_coord)){
        next_coord_val = state->board[next_coord.row][next_coord.col];
        if (val_is_empty_or_apple(next_coord_val)\
        || coords_are_equal(&snake_rear, &next_coord)){
            next_possible_moves = next_possible_moves | DIR_EAST;
        }
    }

    next_coord = calculate_west_neighbor(&(state->snake_body_front->pos));
    if (coord_in_board(&next_coord)){
        next_coord_val = state->board[next_coord.row][next_coord.col];
        if (val_is_empty_or_apple(next_coord_val)\
        || coords_are_equal(&snake_rear, &next_coord)){
            next_possible_moves = next_possible_moves | DIR_WEST;
        }
    }

    return next_possible_moves;
}

int move_is_single(unsigned int move){
    return ( (move == 1) && (move != 2) && (move != 4) && (move != 8) )\
    || ( (move != 1) && (move == 2) && (move != 4) && (move != 8) )\
    || ( (move != 1) && (move != 2) && (move == 4) && (move != 8) )\
    || ( (move != 1) && (move != 2) && (move != 4) && (move == 8) );
}

void duplicate_state_in_place(struct GameState *state, struct GameState *new_state){

    new_state->next_move = state->next_move;

    new_state->score = state->score;

    new_state->apple_coord.row = state->apple_coord.row;
    new_state->apple_coord.col = state->apple_coord.col;
    
    const int rows = 15, cols = 17;
    for (int r = 0; r < rows; ++r) {
        for (int c = 0; c < cols; ++c) {
            new_state->board[r][c] = state->board[r][c];
        }
    }

    struct Node *current_node = state->snake_body_rear;

    while (current_node){
        struct Node *new_node = malloc(sizeof(struct Node));
        if (!new_node) {
            fprintf(stderr, "malloc failed for snake node\n");
            return; // caller must handle partial snake if this happens
        }

        new_node->pos.row = current_node->pos.row;
        new_node->pos.col = current_node->pos.col;
        new_node->next = NULL;

        if (new_state->snake_body_front) {
            new_state->snake_body_front->next = new_node;
        } else {
            new_state->snake_body_rear = new_node; // first node
        }
        new_state->snake_body_front = new_node;

        current_node = current_node->next;
    }
}

void calculate_next_state_in_place(unsigned int next_move, struct GameState *state){
    if(!move_is_single(next_move))
        fprintf(stderr, "calculate_next_node recieved invalid move.\n");

    //read snake_rear_coord
    struct Node *cur_snake_body_rear = state->snake_body_rear;
    //mark rear coord as empty on new board
    state->board[cur_snake_body_rear->pos.row][cur_snake_body_rear->pos.col] = 0;
    //remove rear from queue
    state->snake_body_rear = state->snake_body_rear->next;
    free(cur_snake_body_rear);

    //mark front coord as body
    state->board[state->snake_body_front->pos.row][state->snake_body_front->pos.col] = 1;
    //calc neighbor and mark as head, update head and add new head to queue
    
    struct Coord next_coord;
    switch(next_move){
        case DIR_NORTH:
            next_coord = calculate_north_neighbor(&(state->snake_body_front->pos));
            break;

        case DIR_SOUTH:
            next_coord = calculate_south_neighbor(&(state->snake_body_front->pos));
            break;

        case DIR_EAST:
            next_coord = calculate_east_neighbor(&(state->snake_body_front->pos));
            break;

        case DIR_WEST:
            next_coord = calculate_west_neighbor(&(state->snake_body_front->pos));
            break;
    }
    //mark head in board!
    state->board[next_coord.row][next_coord.col] = HEAD;
    //iff head coord is apple, increment score, new apple coord -1,-1
    if (state->board[next_coord.row][next_coord.col] == APPLE){
        state->score += 1;
        state->apple_coord.row = -1;
        state->apple_coord.col = -1;
    }
    
    struct Node *new_node = malloc(sizeof(struct Node));
    if (!new_node) {
        fprintf(stderr, "malloc failed for snake node\n");
        return; // caller must handle partial snake if this happens
    }

    new_node->pos.row = next_coord.row;
    new_node->pos.col = next_coord.col;
    new_node->next = NULL;
    
    state->snake_body_front->next = new_node;
    state->snake_body_front = new_node;

    //state->next_move = calculate_possible_moves(state);
    state->next_move = 0;
}

struct Coord build_logic_blue_ratios(struct GameState *state, double (*ratios)[17]){

    for (int r = 0; r < ROWS; r++) {
        for (int c = 0; c < COLS; c++) {
            ratios[r][c] = 0.0;
        }
    }

    struct Coord next_coord;
    next_coord = calculate_north_neighbor(&(state->snake_body_front->pos));
    if (coord_in_board(&next_coord))
        ratios[next_coord.row][next_coord.col] = 0.25;
    next_coord = calculate_south_neighbor(&(state->snake_body_front->pos));
    if (coord_in_board(&next_coord))
        ratios[next_coord.row][next_coord.col] = 0.25;
    next_coord = calculate_east_neighbor(&(state->snake_body_front->pos));
    if (coord_in_board(&next_coord))
        ratios[next_coord.row][next_coord.col] = 0.25;
    next_coord = calculate_west_neighbor(&(state->snake_body_front->pos));
    if (coord_in_board(&next_coord))
        ratios[next_coord.row][next_coord.col] = 0.25;

    struct Node *current_node = state->snake_body_rear;
    struct Node *last_node = NULL;
    struct Node *nexto_last_node = NULL;

    while (current_node){
        ratios[current_node->pos.row][current_node->pos.col] = 1.0;
        nexto_last_node = last_node;
        last_node = current_node;
        current_node = current_node->next;
    }

    ratios[state->snake_body_rear->pos.row][state->snake_body_rear->pos.col] = 0.25;
    struct Coord last_head_coord;
    last_head_coord.row = nexto_last_node->pos.row;
    last_head_coord.col = nexto_last_node->pos.col;

    return last_head_coord;
}

MaxHeap *mul_ratio_matrices(double (*read_ratios)[COLS], double (*logic_ratios)[COLS], double (*result_ratios)[COLS]){
    MaxHeap *max_coords_result = heap_create(64);

    for (int r = 0; r < ROWS; r++) {
        for (int c = 0; c < COLS; c++) {
            double value = read_ratios[r][c] * logic_ratios[r][c];
            result_ratios[r][c] = value;
            if (value != 0){
                heap_push(max_coords_result, value, r, c);
            }
        }
    }
   return max_coords_result; 
}

unsigned int determine_move(struct GameState *state, MaxHeap *h, struct Coord *last_head_coord){

    unsigned int detected_move = 0;
    unsigned int mask = 15;

    struct Coord north_neighbor = calculate_north_neighbor(&(state->snake_body_front->pos));
    struct Coord south_neighbor = calculate_south_neighbor(&(state->snake_body_front->pos));
    struct Coord east_neighbor = calculate_east_neighbor(&(state->snake_body_front->pos));
    struct Coord west_neighbor = calculate_west_neighbor(&(state->snake_body_front->pos));

    HeapNode cur_hnode;

    for (int i = 0; i < state->score + 4; ++i){
        if (h->size > 0){
            cur_hnode = heap_pop(h);
            if (coords_are_equal(&cur_hnode.coord, &state->snake_body_rear->pos)){
                mask = 0;
            }
            if (coords_are_equal(&north_neighbor, &cur_hnode.coord) &&\
                !(coords_are_equal(&north_neighbor, last_head_coord))){
                detected_move = DIR_NORTH;
                break;
                }
            if (coords_are_equal(&south_neighbor, &cur_hnode.coord) &&\
                !(coords_are_equal(&south_neighbor, last_head_coord))){
                detected_move = DIR_SOUTH;
                break;
                }
            if (coords_are_equal(&east_neighbor, &cur_hnode.coord) &&\
                !(coords_are_equal(&east_neighbor, last_head_coord))){
                detected_move = DIR_EAST;
                break;
                }
            if (coords_are_equal(&west_neighbor, &cur_hnode.coord) &&\
                !(coords_are_equal(&west_neighbor, last_head_coord))){
                detected_move = DIR_WEST;
                break;
                }
            }
    }
    return detected_move & mask;
}

/*==========================================================================  
 * Expansion nodes 
 *  ========================================================================*/

struct ExpansionNode {
    struct GameState *state;
    struct ExpansionNode *next;
};

