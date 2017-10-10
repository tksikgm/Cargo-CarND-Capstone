from styx_msgs.msg import TrafficLight
import rospy
import tensorflow as tf
import numpy as np
import time
from PIL import Image

TRAFFIC_CLASSIFIER_MDOEL_PATH = './model/frozen_inference_graph_sim.pb'
DETECTION_THRESHOLD = 0.5

class TLClassifier(object):
    def __init__(self):
	self.state = TrafficLight.UNKNOWN

        #TODO load classifier

	self.detection_graph = tf.Graph()

        with self.detection_graph.as_default():
            od_graph_def = tf.GraphDef()

            with tf.gfile.GFile(TRAFFIC_CLASSIFIER_MDOEL_PATH, 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name='')

    def get_classification(self, image):
        """Determines the color of the traffic light in the image

        Args:
            image (cv::Mat): image containing the traffic light

        Returns:
            int: ID of traffic light color (specified in styx_msgs/TrafficLight)

        """
        time_start = time.time()
        #TODO implement light color prediction
        with self.detection_graph.as_default():
            with tf.Session(graph=self.detection_graph) as sess:
                # Definite input and output Tensors for detection_graph
                image_tensor = self.detection_graph.get_tensor_by_name('image_tensor:0')

                # Each box represents a part of the image where a particular object was detected.
                detection_boxes = self.detection_graph.get_tensor_by_name('detection_boxes:0')

                # Each score represent how level of confidence for each of the objects.
                # Score is shown on the result image, together with the class label.
                detection_scores = self.detection_graph.get_tensor_by_name('detection_scores:0')
                detection_classes = self.detection_graph.get_tensor_by_name('detection_classes:0')
                num_detections = self.detection_graph.get_tensor_by_name('num_detections:0')

                image_np = self.__preprocess_image(image)
                # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
                image_np_expanded = np.expand_dims(image_np, axis=0)

                time0 = time.time()

                # Actual detection.
                (boxes, scores, classes, num) = sess.run(
                    [detection_boxes, detection_scores, detection_classes, num_detections],
                    feed_dict={image_tensor: image_np_expanded})

                time1 = time.time()
                #print("Time in milliseconds", (time1 - time0) * 1000)
                #print(boxes, scores, classes)

        output = self.__postprocessing_detected_box(scores[0], classes[0])
        rospy.logerr('Time in milliseconds' + str(time1-time0)+' Result:'+self.__traffic_id_to_name(output))
        return output


    def __preprocess_image(self, image):
        image = Image.fromarray(image)
        # image.save('check'+str(time.time())+'.jpg')
        (im_width, im_height) = image.size
        return np.array(image.getdata()).reshape(
            (im_height, im_width, 3)).astype(np.uint8)

    def __postprocessing_detected_box(self, scores, classes):
        candidate_num = 5
        vote = []
        for i in range(candidate_num):
            if scores[i] < DETECTION_THRESHOLD:
                break
            vote.append(self.__label_map_to_traffic_light(int(classes[i])))
        rospy.logerr('Votes' + str(vote))
        if vote:
            return max(vote, key=vote.count)
        else:
            return 4


    def __label_map_to_traffic_light(self, label_id):
        traffic_label = int(label_id) - 1
        if traffic_label in [0, 1, 2, 4]:
            return  traffic_label
        return 4

    def __traffic_id_to_name(self, traffic_id):
        traffic_light_names = ['Red','Yellow','Green','Error','Unknown']
        return traffic_light_names[traffic_id]
        #if  label_id in [1,2,3,5]:

        # label_map = ['Green', 'Red', 'GreenLeft', 'GreenRight', 'RedLeft', 'RedRight', 'Yellow', 'off', 'RedStraight',
        #              'GreenStraight', 'GreenStraightLeft', 'GreenStraightRight', 'RedStraightLeft', 'RedStraightRight']
        # if 0 < label_id <= len(label_map):
        #     light = label_map[label_id-1]
        #     if light.startswith('Green'):
        #         return 2
        #     elif light.startswith('Red'):
        #         return 0
        #     elif light.startswith('Yellow'):
        #         return 1
        #     else:
        #         return 4 # off
        # else:
        #     return 4
