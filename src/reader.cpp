#include <stdint.h>
#include <iostream>
#include <cstring>
#include <fstream>
#include <chrono>
#include <thread>
#include <math.h>
#include <stdlib.h>
#include <errno.h>

#define X_MAX             32
#define Y_MAX             24
#define IMAGE_PIXELS      X_MAX * Y_MAX


int main (int argc, char** argv) {
  static float raw[IMAGE_PIXELS];

  // RAW binary data is saved in a temporary dump
  FILE *rawfp = fopen("/tmp/dataset.bin", "rb");
  if (rawfp == NULL) exit(-1);
  int bytes = 1;

  while (bytes > 0 ) {
    bytes = fread(&raw, sizeof(float), IMAGE_PIXELS, rawfp);
    fprintf(stdout, "> read %d B, sizeof(float) = %d\n", bytes, sizeof(float));
    for (int i = 0; i < IMAGE_PIXELS; i++) fprintf (stdout, "%.3f ", raw[i]);
    getchar();
  }

  fclose(rawfp);

}
