import pika
import time
import numpy as np
import cv2
import json

class MessageQueue():
    def __init__(self, queue_name):
        self.queue = queue_name
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=queue_name)
        print(f"{queue_name} declared")
    
    def get_msg(self, queue_name=""):
        return self.channel.basic_get(queue=self.queue, auto_ack=True)
    
    def add_msg(self, body, queue_name="") -> bool:
        print(f"{self.queue} sending message")
        if type(body) == str:
            # String message
            self.channel.basic_publish(exchange="", routing_key=self.queue, body=body)
            return True
        if type(body) == np.ndarray:
            # JPG message
            encoded = cv2.imencode(".jpg", body)[1].tobytes()
            self.channel.basic_publish(exchange="", routing_key=self.queue, body=encoded)
            return True
        if type(body) == dict:
            body = json.dumps(body)
            self.channel.basic_publish( exchange="", routing_key=self.queue, body=body)
            return True
        return False

    def add_queue(self, queue_name) -> bool:
        if queue_name == self.queue:
            return False
        if type(self.channel) != dict:
            self.channel = {self.queue : self.channel}
        elif queue_name in self.channel:
            return False
        self.channel[queue_name] = self.connection.channel()
        self.channel[queue_name].queue_declare(queue=queue_name)

    def get_blocking_msg(self, callback):
        self.channel.basic_consume(queue=self.queue, on_message_callback=callback, auto_ack=True)
        print(f"{self.queue} starting consume")
        return self.channel.start_consuming()

if __name__ == "__main__":
    rq = MessageQueue("hello")
    while True:
        method_frame, header_frame, body = rq.get_msg()
        print(method_frame, header_frame, body)
        if method_frame:
            img = cv2.imdecode(np.frombuffer(body, dtype=np.uint8), cv2.IMREAD_COLOR)
            print(img)

        time.sleep(2)

    # Sending message 
    # numpy jpg array: jpg
    # encoded = cv2.imencode(".jpg", jpg)[1].tobytes()
    # mq.add_msg(encoded)
    # decoded = cv2.imdecode(np.frombuffer(body, dtype=np.uint8), cv2.IMREAD_COLOR)