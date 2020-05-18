I2C_MODE = LINUX
I2C_LIBS =
#I2C_LIBS = -lbcm2835
SRC_DIR = src/
BUILD_DIR = .build/
LIB_DIR = lib/
STREAMER_BIN = mlx90640-streamer
RAWRGB_BIN = rawrgb
READER_BIN = mlx90640-reader
SERVICE_USER = mlx90640

streamer = streamer
streamer_objects = $(addsuffix .o,$(addprefix $(SRC_DIR), $(streamer)))
streamer_output = $(addprefix $(BUILD_DIR), $(streamer))

reader = reader
reader_objects = $(addsuffix .o,$(addprefix $(SRC_DIR), $(reader)))
reader_output = $(addprefix $(BUILD_DIR), $(reader))

rawrgb = rawrgb
rawrgb_objects = $(addsuffix .o,$(addprefix $(SRC_DIR), $(rawrgb)))
rawrgb_output = $(addprefix $(BUILD_DIR), $(rawrgb))


#PREFIX is environment variable, but if it is not set, then set default value
ifeq ($(PREFIX),)
	PREFIX = /usr/local
endif

ifeq ($(I2C_MODE), LINUX)
	I2C_LIBS =
endif

all: init libMLX90640_API.a libMLX90640_API.so streamer reader rawrgb post

pristine: all clean-objects

init:
	mkdir -p $(BUILD_DIR)

post:
	mv -f libMLX90640_API.* 			$(BUILD_DIR).
	mv -f $(BUILD_DIR)$(streamer) $(BUILD_DIR)$(STREAMER_BIN)
	mv -f $(BUILD_DIR)$(reader) 	$(BUILD_DIR)$(READER_BIN)

streamer: $(streamer_output)
reader: $(reader_output)
rawrgb: $(rawrgb_output)

libMLX90640_API.so: lib/MLX90640_API.o lib/MLX90640_$(I2C_MODE)_I2C_Driver.o
	$(CXX) -fPIC -shared $^ -o $@ $(I2C_LIBS)

libMLX90640_API.a: lib/MLX90640_API.o lib/MLX90640_$(I2C_MODE)_I2C_Driver.o
	ar rcs $@ $^
	ranlib $@

lib/MLX90640_API.o lib/MLX90640_RPI_I2C_Driver.o lib/MLX90640_LINUX_I2C_Driver.o : CXXFLAGS+=-fPIC -I $(LIB_DIR) -shared $(I2C_LIBS)

$(streamer_objects) : CXXFLAGS+=-std=c++11
$(streamer_output) : CXXFLAGS+=-I$(LIB_DIR) -std=c++11

$(reader_objects) : CXXFLAGS+=-std=c++11
$(reader_output) : CXXFLAGS+=-I$(LIB_DIR) -std=c++11

$(rawrgb_objects) : CXXFLAGS+=-std=c++11
$(rawrgb_output) : CXXFLAGS+=-I$(LIB_DIR) -std=c++11

lib/interpolate.o : CC=$(CXX) -std=c++11

$(BUILD_DIR)streamer: $(SRC_DIR)streamer.o libMLX90640_API.a
	$(CXX) -L$(LIB_DIR) $^ -o $@ $(I2C_LIBS)

$(BUILD_DIR)reader: $(SRC_DIR)reader.o libMLX90640_API.a
	$(CXX) -L$(LIB_DIR) $^ -o $@ $(I2C_LIBS)

$(BUILD_DIR)rawrgb: $(SRC_DIR)rawrgb.o libMLX90640_API.a
	$(CXX) -L$(LIB_DIR) $^ -o $@ $(I2C_LIBS)

bcm2835: bcm2835-1.55
	wget http://www.airspayce.com/mikem/bcm2835/bcm2835-1.55.tar.gz
	mv -f bcm2835-1.55.tar.gz $(BUILD_DIR).
	cd $(BUILD_DIR); tar xzvf bcm2835-1.55.tar.gz
	cd bcm2835-1.55; ./configure; make; sudo make install

clean-objects:
	rm -f $(SRC_DIR)*.o
	rm -f $(LIB_DIR)*.o
	rm -f *.o
	rm -f *.so
	rm -f *.a
	rm -f *.gch

clean: clean-objects
	rm -f $(streamer_output)

purge: clean
	rm -Rf $(BUILD_DIR)

install: install-libs
	install -d $(DESTDIR)$(PREFIX)/bin/
	install -m 550 $(BUILD_DIR)$(STREAMER_BIN) $(DESTDIR)$(PREFIX)/bin/$(STREAMER_BIN)
	install -m 550 $(BUILD_DIR)$(RAWRGB_BIN) $(DESTDIR)$(PREFIX)/bin/$(RAWRGB_BIN)
	chown $(SERVICE_USER):$(SERVICE_USER) $(DESTDIR)$(PREFIX)/bin/$(STREAMER_BIN)

install-libs:
	install -d $(DESTDIR)$(PREFIX)/lib/
	install -m 644 $(BUILD_DIR)libMLX90640_API.a $(DESTDIR)$(PREFIX)/lib/
	install -m 644 $(BUILD_DIR)libMLX90640_API.so $(DESTDIR)$(PREFIX)/lib/
	install -d $(DESTDIR)$(PREFIX)/include/MLX90640/
	install -m 644 $(LIB_DIR)/*.h $(DESTDIR)$(PREFIX)/include/MLX90640/
	ldconfig
