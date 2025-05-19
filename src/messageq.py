import pika
import time

class MessageQueue():
    def __init__(self, queue_name, blocking=False):
        self.queue = queue_name
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.channel = self.connection.channel()
        print("Starting queue")
        self.channel.queue_declare(queue=queue_name)
    
    def get_msg(self, queue_name=""):
        return self.channel.basic_get(queue=self.queue, auto_ack=True)
    
    def add_msg(self, body, queue_name=""):
        self.channel.basic_publish(exchange="", routing_key=self.queue, body=body)

    def add_queue(self, queue_name) -> bool:
        if queue_name == self.queue:
            return False
        if type(self.channel) != dict:
            self.channel = {self.queue : self.channel}
        elif queue_name in self.channel:
            return False
        self.channel[queue_name] = self.connection.channel()
        self.channel[queue_name].queue_declare(queue=queue_name)



if __name__ == "__main__":
    rq = MessageQueue("hello")
    while True:
        method_frame, header_frame, body = rq.get_msg()
        print(method_frame, header_frame, body)
        if method_frame:
            print("MSG RECIEVED")
        time.sleep(2)