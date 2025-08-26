#include "firrtl-cover.h"

typedef struct {
  uint8_t #COVER_TYPE#[#COVER_POINT_NUM#];
} CoverPoints;
static CoverPoints coverPoints;

extern "C" void v_cover_#COVER_TYPE#(uint64_t index) {
  coverPoints.#COVER_TYPE#[index] = 1;
}

static const char *#COVER_TYPE#_NAMES[] = {
#COVER_POINT_NAMES#
};

FIRRTLCoverPointParam firrtl_cover[1] = {
  { { coverPoints.#COVER_TYPE#, #COVER_POINT_NUM#UL, "#COVER_TYPE#", #COVER_TYPE#_NAMES }, true },
};
