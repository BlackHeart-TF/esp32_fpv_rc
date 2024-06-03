class RingBuffer {
public:
    RingBuffer(int capacity) : buffer(new char[capacity]), capacity(capacity), size(0), head(0), tail(0) {}

    ~RingBuffer() {
        delete[] buffer;
    }

    void add(char data) {
        if (size == capacity) {
            // Buffer full, overwrite oldest data
            tail = (tail + 1) % capacity;
        } else {
            ++size;
        }
        buffer[head] = data;
        head = (head + 1) % capacity;
    }

    void reset(){
      head = 0;
      tail = 0;
      size = 0;
      //Serial.printf("size reset: %d",size);
    }

    char get(int index) {
        if (index < 0 || index >= size) {
            // Invalid index
            return '\0'; // Or throw an exception
        }
        int reversedIndex = (head - index - 1 + capacity) % capacity;
        return buffer[reversedIndex];
        //return buffer[(tail + index) % capacity];
    }

    int getSize() {
        return size;
    }

private:
    char* buffer;
    int capacity;
    int size;
    int head;
    int tail;
};
