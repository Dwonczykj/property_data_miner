
# ~ https://medium.com/@naseer1015922/5-killer-python-scripts-for-automation-part-2-33d7aa84cedc
import cv2

# Load the cascade classifier for face detection
face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

# Load the image
img = cv2.imread("image.jpg")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Detect faces
faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

# Draw rectangles around the faces
for (x, y, w, h) in faces:
    cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)

# Show the image

cv2.imshow("Faces", img)
cv2.waitKey(0)
cv2.destroyAllWindows()
