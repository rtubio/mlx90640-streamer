#include <stdint.h>
#include <iostream>
#include <cstring>
#include <fstream>
#include <chrono>
#include <thread>
#include <math.h>
#include <stdlib.h>
#include <errno.h>
#include <syslog.h>
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


#define MLX_I2C_ADDR 0x33

#define IMAGE_SCALE 5

// Valid frame rates are 1, 2, 4, 8, 16, 32 and 64
// The i2c baudrate is set to 1mhz to support these
#define FPS 16
#define FRAME_TIME_MICROS (1000000/FPS)

// Despite the framerate being ostensibly FPS hz
// The frame is often not ready in time
// This offset is added to the FRAME_TIME_MICROS
// to account for this.
#define OFFSET_MICROS 850

#define PIXEL_SIZE_BYTES 3
#define IMAGE_SIZE 768*PIXEL_SIZE_BYTES
#define X_MAX                 32
#define Y_MAX                 24
#define IMAGE_PIXELS      X_MAX * Y_MAX

void put_pixel_false_colour(char *image, int x, int y, double v) {
    // Heatmap code borrowed from: http://www.andrewnoske.com/wiki/Code_-_heatmaps_and_color_gradients
    const int NUM_COLORS = 7;
    static float color[NUM_COLORS][3] = { {0,0,0}, {0,0,1}, {0,1,0}, {1,1,0}, {1,0,0}, {1,0,1}, {1,1,1} };
    int idx1, idx2;
    float fractBetween = 0;
    float vmin = 5.0;
    float vmax = 50.0;
    float vrange = vmax-vmin;
    int offset = (y*32+x) * PIXEL_SIZE_BYTES;

    v -= vmin;
    v /= vrange;
    if(v <= 0) {idx1=idx2=0;}
    else if(v >= 1) {idx1=idx2=NUM_COLORS-1;}
    else
    {
        v *= (NUM_COLORS-1);
        idx1 = floor(v);
        idx2 = idx1+1;
        fractBetween = v - float(idx1);
    }

    int ir, ig, ib;


    ir = (int)((((color[idx2][0] - color[idx1][0]) * fractBetween) + color[idx1][0]) * 255.0);
    ig = (int)((((color[idx2][1] - color[idx1][1]) * fractBetween) + color[idx1][1]) * 255.0);
    ib = (int)((((color[idx2][2] - color[idx1][2]) * fractBetween) + color[idx1][2]) * 255.0);

    //put calculated RGB values into image map
    image[offset] = ir;
    image[offset + 1] = ig;
    image[offset + 2] = ib;


}

int main(int argc, char *argv[]){

    static uint16_t eeMLX90640[832];
    float emissivity = 0.8;
    uint16_t frame[834];
    static char image[IMAGE_SIZE];
    static float pixels[IMAGE_PIXELS];
    static float mlx90640To[IMAGE_PIXELS];
    float eTa;
    static uint16_t data[768*sizeof(float)];
    static int fps = FPS;
    static long frame_time_micros = FRAME_TIME_MICROS;
    char *p;

    openlog("rawrgb", LOG_PID, LOG_SYSLOG);

    if(argc > 1){
        fps = strtol(argv[1], &p, 0);
        if (errno !=0 || *p != '\0') {
            syslog(LOG_ERR, "Invalid framerate\n");
            return 1;
        }
        frame_time_micros = 1000000/fps;
    }

    auto frame_time = std::chrono::microseconds(frame_time_micros + OFFSET_MICROS);

    MLX90640_SetDeviceMode(MLX_I2C_ADDR, 0);
    MLX90640_SetSubPageRepeat(MLX_I2C_ADDR, 0);
    switch(fps){
        case 1:
            MLX90640_SetRefreshRate(MLX_I2C_ADDR, 0b001);
            break;
        case 2:
            MLX90640_SetRefreshRate(MLX_I2C_ADDR, 0b010);
            break;
        case 4:
            MLX90640_SetRefreshRate(MLX_I2C_ADDR, 0b011);
            break;
        case 8:
            MLX90640_SetRefreshRate(MLX_I2C_ADDR, 0b100);
            break;
        case 16:
            MLX90640_SetRefreshRate(MLX_I2C_ADDR, 0b101);
            break;
        case 32:
            MLX90640_SetRefreshRate(MLX_I2C_ADDR, 0b110);
            break;
        case 64:
            MLX90640_SetRefreshRate(MLX_I2C_ADDR, 0b111);
            break;
        default:
            syslog(LOG_ERR, "Unsupported framerate\n");
            return 1;
    }
    MLX90640_SetChessMode(MLX_I2C_ADDR);

    paramsMLX90640 mlx90640;
    MLX90640_DumpEE(MLX_I2C_ADDR, eeMLX90640);
    MLX90640_SetResolution(MLX_I2C_ADDR, 0x03);
    MLX90640_ExtractParameters(eeMLX90640, &mlx90640);
    int frame_no = 0;

    while (1){

        auto start = std::chrono::system_clock::now();
        MLX90640_GetFrameData(MLX_I2C_ADDR, frame);
        MLX90640_InterpolateOutliers(frame, eeMLX90640);

        eTa = MLX90640_GetTa(frame, &mlx90640); // Sensor ambient temprature
        MLX90640_CalculateTo(frame, &mlx90640, emissivity, eTa, mlx90640To); //calculate temprature of all pixels, base on emissivity of object

        //Fill image array with false-colour data (raw RGB image with 24 x 32 x 24bit per pixel)
        for (int y = 0; y < 24; y++) {
            for (int x = 0; x < 32; x++) {
                float val = mlx90640To[32 * (23-y) + x];
                put_pixel_false_colour(image, x, y, val);
                pixels[x + 32*y] = val;
            }
        }

        //wite RGB image to stdout
        fwrite(&image, 1, IMAGE_SIZE, stdout);
        fflush(stdout); // flush now to stdout

        fwrite(&pixels, sizeof(float), IMAGE_PIXELS, stderr);
        fflush(stderr);  // flush now to file

        auto end = std::chrono::system_clock::now();
        auto elapsed = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
        std::this_thread::sleep_for(std::chrono::microseconds(frame_time - elapsed));

        syslog(LOG_INFO, ">>> frame_no = %d\n", frame_no++);

    }

    closelog();
    return 0;

}
