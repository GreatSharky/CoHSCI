from messageq import MessageQueue

# Write control/state machine that tracks program state.
# Roles:
#   1. Trigger capture
#   2. Give updates to webcam
#   3. Process classifictions
#   4. Command robot
#  
# Could rewrite webcam to only do the wecam sequence inside the state machine.
# That way the control would trigger capture, change capture, mask and classification flags.
# It could change box color, it could send messages, it could change text.
# 
# Other option is to send stuff over message queue to webcam like get_gesture which would trigger
# webcam -> segmentor -> classifier -> validator -> control pipeline.
# During pipeline control could update send webcam status updates on message queue.
# Webcam should then be refactored. #

class Control():
    def __init__(self):
        self.webcam = MessageQueue("control-webcam")
        self.segmentor = MessageQueue("control-segmentor")
        self.classifier = MessageQueue("control-classifier")
        
        self.do_capture = False

    def control_cycle(self):
        wc_method, wc_props, wc_body = self.webcam.get_msg() 
        self.webcam_callback(None, wc_method, wc_props, wc_body)
        sg_method, sg_props, sg_body = self.segmentor.get_msg()
        self.segmentor_callback(None, sg_method, sg_props, sg_body)
        cl_method, cl_props, cl_body = self.classifier.get_msg()
        self.classifier_callback(None, cl_method, cl_props, cl_body)

    def classifier_callback(self, ch, method, properties, body):
        if method != None:
            # Classifier status changed
            # Possible classifier statuses: image recieved, classifing, waiting for validation,
            # validation failed, validated
            return
        
    def validator_callback(self, ch, method, properties, body):
        if method != None:
            # Validator status changed
            # Possible validator sstatuses: image text recieved, validation failed, 
            # validation success#
            return
        
    def robot_callback(self, ch, method, properties, body):
        if method != None:
            # Robot status changed
            # Possible robot status: action recieved, action started, action done#
            return
    
    def segmentor_callback(self, ch, method, properties, body):
        if method != None:
            # segmentor status changed
            # Possible segmentor statuses: image recieved, mask ready
            return
    
    def webcam_callback(self, ch, method, properties, body):
        if method != None:
            # Webcam status changed
            # Possible webcam status: Capture made, Capture requested, User ready
            msg = body.decode("utf-8")
            

    def message_classifier(self, body):
        return
    
    def message_segmentor(self):
        return
    
    def message_weacam(self):
        # Status changes in the system are relayed to the operator with text added to the webcam screen 
        # #
        return

if __name__ == "__main__":
    state_machine = Control()
    while True:
        x = state_machine.webcam.get_msg()
        if x[0] != None:
            print(x)
