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
    
    def get_msg(self):
        method, properties, body = self.channel.basic_get(self.queuem, auto_ack=True)
        body = json.loads(body)
        if type(body) == dict:
            if "img" in body:
                array = np.array([np.uint8(x) for x in body["img"]])
                body["img"] = cv2.imdecode(array, cv2.IMREAD_COLOR)[1]
        return method, properties, body
    
    def add_msg(self, body) -> bool:
        if type(body) == dict:
            if "img" in body:
                body["img"] = [int(x) for x in body["img"]]
        pkg = json.dumps(body)
        return self.channel.basic_publish(exchange="", routing_key=self.queue, body=pkg)
        

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