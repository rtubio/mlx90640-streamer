#include <stdint.h>
#include <iostream>
#include <cstring>
#include <fstream>
#include <chrono>
#include <thread>
#include <math.h>
#include <stdlib.h>
#include <errno.h>
#include "MLX90640_API.h"

/*
 * rawrgb
 * ======
 * outputs raw false-color 24bit RGB stream of 24x32 pixels to
 * stdout
 *
 * streaming to remote host with GStreamer tools
 * ----------------------------------------------
 *
 * This is modified example code, which outputs a raw data stream of
 * false-colour thermal images from the sensor to STDOUT.
 * Each image is encoded in RGB (24bit) and has a width of 24 / height
 * of 32 pixels. Thus a single image consumes 2304 bytes and is written
 * at once to stdout.
 *
 * The data could be streamed with gstreamer to visualize it on a remote
 * host, without utilizing framebuffers. This allows to move the CPU
 * intensive encoding to the remote host (nice for headless setups with
 * Pi Zero W).
 *
 * A valid receiver in gstreamer could be started like this on a
 * receiving remote host:
 *
 * $ gst-launch-1.0 udpsrc blocksize=2304 port=5000 ! rawvideoparse use-sink-caps=false width=32 height=24 format=rgb framerate=16/1 ! videoconvert ! videoscale ! video/x-raw,width=640,height=480 ! autovideosink
 *
 * The command above reads 2304 byte blockes from UDP port 5000,
 * interprets the data as raw video with "width=32 height=24 format=rgb",
 * scales it up to 640x480 pixels (with default interpolation) and
 * renders it to default output. So most of the processing is done on the
 * remote host.
 *
 * The sender, which is running on the device with mlx90640 connected,
 * could use the following command (assuming the receiver IP is
 * 172.16.0.2):
 *
 * $ ./rawrgb | gst-launch-1.0 fdsrc blocksize=2304 ! udpsink host=172.16.0.2 port=5000
 *
 * The sender reads the output generated by the `rawrgb` binary on stdin
 * and forwards it to the remote host 172.16.0.2 on port 5000. There's
 * no further processing done on the sender's end (source host).
 *
 * Note1:
 * For the example above, the receiver should be started first.
 * As the stream isn't encoded, data loss (during UDP transfer) or frame
 * starts couldn't be detected by the receiver. Both would lead to
 * offseted images, if the stream to the receiver doesn't start with a
 * valid frame.
 *
 * Note2:
 * The code was tested on a Raspberry Pi 0 W, the bcm2835 driver
 * was used for I2C communication. Unfortunately, the
 * `MLX90640_GetFrameData` command produces CPU load >60% in this setup.
 * The Linux system used, wasn't a Raspbian but another Debian derivate,
 * which isn't compiled with hard float support. Anyways, the method
 * `MLX90640_GetFrameData` doesn't involve float calculations.
 * The float based false-colour calculations and temprature translation
 * don't impact performance too much on soft float. Seems the limiting
 * factor is the I2C access.
 *
 */

// Specific MLX90640 constants
#define MLX_I2C_ADDR        0x33
#define MLX_EE_BUFFER_LEN   832
#define MLX_FRAME_LEN       834

#define MLX_RR_1FPS         0b001
#define MLX_RR_2FPS         0b010
#define MLX_RR_4FPS         0b011
#define MLX_RR_8FPS         0b100
#define MLX_RR_16FPS        0b101
#define MLX_RR_32FPS        0b110
#define MLX_RR_64FPS        0b111

// Valid frame rates are 1, 2, 4, 8, 16, 32 and 64
// The i2c baudrate is set to 1mhz to support these
#define DEFAULT_FPS           16
#define DEFAULT_REFRESH_RATE  0b001
#define FRAME_TIME_MICROS     ( 1000000 / DEFAULT_FPS )
#define VMIN                  -15.0
#define VMAX                  +120.0
#define TARGET_EMISSIVITY     0.85    // graphite
#define X_MAX                 32
#define Y_MAX                 24

// Configurable resolutions
#define RESOLUTION_16bit      0x00
#define RESOLUTION_17bit      0x01
#define RESOLUTION_18bit      0x01
#define RESOLUTION_19bit      0x03

// Despite the framerate being ostensibly DEFAULT_FPS hz, the frame is often not ready in time
// This offset is added to the FRAME_TIME_MICROS to account for this.
#define OFFSET_MICROS     850

// Image sizing numbers
// pixels X_MAX * Y_MAX
// max resolution: 16 to 19 bits > 2 to 3 bytes : always 3 bytes (oversized for lowest resolution)
#define PIXEL_SIZE_B      3
#define IMAGE_PIXELS      X_MAX * Y_MAX
#define IMAGE_SIZE        IMAGE_PIXELS * PIXEL_SIZE_B
#define RAW_IMAGE_SIZE    IMAGE_PIXELS * sizeof(float)


void pixel2colour(char *image, int x, int y, double v) {

    // Heatmap code borrowed from: http://www.andrewnoske.com/wiki/Code_-_heatmaps_and_color_gradients
    const static int NUM_COLORS = 7;
    static float color[NUM_COLORS][3] = { {0,0,0}, {0,0,1}, {0,1,0}, {1,1,0}, {1,0,0}, {1,0,1}, {1,1,1} };
    int   idx1, idx2;
    float fractBetween  = 0;
    float vmin          = VMIN;
    float vmax          = VMAX;
    float vrange        = vmax-vmin;
    int   offset        = (y*X_MAX+x) * PIXEL_SIZE_B;

    v -= vmin;
    v /= vrange;

    if      (v <= 0) idx1 = idx2 = 0;
    else if (v >= 1) idx1 = idx2 = (NUM_COLORS - 1);
    else {
        v *= (NUM_COLORS - 1);
        idx1 = floor(v);
        idx2 = idx1 + 1;
        fractBetween = v - float(idx1);
    }

    //put calculated RGB values into image map
    image[offset + 0] = (int)((((color[idx2][0] - color[idx1][0]) * fractBetween) + color[idx1][0]) * 255.0);
    image[offset + 1] = (int)((((color[idx2][1] - color[idx1][1]) * fractBetween) + color[idx1][1]) * 255.0);
    image[offset + 2] = (int)((((color[idx2][2] - color[idx1][2]) * fractBetween) + color[idx1][2]) * 255.0);

}

float read_args(int argc, char **argv, bool *debug) {

  fprintf(stdout, "AAA");
  if (argc < 1) {
    fprintf(stderr, "Wrong arguments, FPS needs to be specified, argv = %s\n", argv);
    exit(-1);
  }

  char *p;
  float fps = 0.0;

  fps = strtol(argv[1], &p, 0);
  if ( errno != 0 || *p != '\0' ) {
      fprintf(stderr, "Wrong arguments, invalid framerate, argv = %s\n", argv);
      exit(-1);
  }

  if (argc > 1) *debug = true;

  return fps;

}

int calculate_refresh_rate(int fps) {

  switch(fps) {
      case 1:
          return MLX_RR_1FPS;
      case 2:
          return MLX_RR_2FPS;
      case 4:
          return MLX_RR_4FPS;
      case 8:
          return MLX_RR_8FPS;
      case 16:
          return MLX_RR_16FPS;
      case 32:
          return MLX_RR_32FPS;
      case 64:
          return MLX_RR_64FPS;
      default:
          fprintf(stderr, "Unsupported framerate: %d\n", fps); exit(-1);
  }

}

void raw2rgb(char* image, float* raw) {

  for ( int y = 0; y < Y_MAX; y++ ) {
      for ( int x = 0; x < X_MAX; x++ ) {
          float raw_pixel = raw[X_MAX * (Y_MAX - 1 - y) + x];
          pixel2colour(image, x, y, raw_pixel);
      }
  }

}

int main(int argc, char **argv) {

    static paramsMLX90640 mlx90640;
    static uint16_t       eeMLX90640  [MLX_EE_BUFFER_LEN];
    static uint16_t       frame       [MLX_FRAME_LEN];
    static char           image       [IMAGE_SIZE];
    static float          raw         [IMAGE_PIXELS];

    static int fps                  = DEFAULT_FPS;
    static int refresh_rate_setting = DEFAULT_REFRESH_RATE;
    static long frame_time_micros   = FRAME_TIME_MICROS;

    bool __DEB__ = false;

    fps                   = read_args(argc, argv, &__DEB__);
    refresh_rate_setting  = calculate_refresh_rate(fps);
    frame_time_micros     = 1e6 / fps;
    auto frame_time       = std::chrono::microseconds(frame_time_micros + OFFSET_MICROS);

    MLX90640_SetRefreshRate     (MLX_I2C_ADDR, refresh_rate_setting);
    MLX90640_SetDeviceMode      (MLX_I2C_ADDR, 0);
    MLX90640_SetSubPageRepeat   (MLX_I2C_ADDR, 0);
    MLX90640_SetChessMode       (MLX_I2C_ADDR);
    MLX90640_DumpEE             (MLX_I2C_ADDR, eeMLX90640);
    MLX90640_SetResolution      (MLX_I2C_ADDR, RESOLUTION_19bit);
    MLX90640_ExtractParameters  (eeMLX90640, &mlx90640);

    while (1){

        auto start    = std::chrono::system_clock::now();

        // Read data from sensor
        MLX90640_GetFrameData         (MLX_I2C_ADDR, frame);
        MLX90640_InterpolateOutliers  (frame, eeMLX90640);

        // Sensor ambient temprature
        // Calculate temprature of all pixels, based on object's emmissivity (WARNING).
        float eTa = MLX90640_GetTa  (frame, &mlx90640);
        MLX90640_CalculateTo        (frame, &mlx90640, TARGET_EMISSIVITY, eTa, raw);

        // Fill image array with false-colour data (raw RGB image with 24 x 32 x 24bit per pixel)
        // Write RGB image to stdout and flush out
        raw2rgb (image, raw);
        if (__DEB__) {
          fwrite  (&image, 1, IMAGE_SIZE, stdout);
          fflush  (stderr);
        } else {
          for (int i = 0; i < IMAGE_PIXELS; i++) fprintf (stdout, "raw = %.6f", raw[i]);
        }

        // RAW binary data is saved in a temporary dump
        FILE *rawfp = fopen("/tmp/dataset.bin", "a");
        if (rawfp == NULL) exit(-1);
        fwrite(&raw, 1, RAW_IMAGE_SIZE,  rawfp);
        fflush(rawfp);
        fclose(rawfp);

        // Estimate time until next frame is ready, and sleep until that
        auto end      = std::chrono::system_clock::now();
        auto elapsed  = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
        std::this_thread::sleep_for(std::chrono::microseconds(frame_time - elapsed));

    }

    return 0;

}
