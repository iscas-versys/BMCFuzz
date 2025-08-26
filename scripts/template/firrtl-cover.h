#ifndef __FIRRTL_COVER_H__
#define __FIRRTL_COVER_H__

#include <cstdint>

typedef struct {
        uint8_t* points;
  const uint64_t total;
  const char*    name;
  const char**   point_names;
} FIRRTLCoverPoint;

typedef struct {
  const FIRRTLCoverPoint cover;
  bool is_feedback;
} FIRRTLCoverPointParam;

extern FIRRTLCoverPointParam firrtl_cover[1];

#endif // __FIRRTL_COVER_H__
