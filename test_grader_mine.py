from imutils.perspective import four_point_transform
from imutils import contours
import imutils
import cv2
import numpy as np
import argparse
import random

def show_images(images, titles, kill_later=True):
    for index, image in enumerate(images):
        cv2.imshow(titles[index], image)
    cv2.waitKey(0)
    if kill_later:
        cv2.destroyAllWindows()

ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required=True, help="path to the input image")
args = vars(ap.parse_args())

ANSWER_KEY = {
    0: 1,
    1: 4,
    2: 0,
    3: 3,
    4: 1
}

# edge detection
image = cv2.imread(args['image'])
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (5, 5), 0)
edged = cv2.Canny(blurred, 75, 200)
show_images([edged], ["Edged"])


# find contours in edge detected image
cnts = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
cnts = imutils.grab_contours(cnts)
docCnt = None

allContourImage = image.copy()
cv2.drawContours(allContourImage, cnts, -1, (0, 0, 255), 3)
print("Total contours found after edge detection {}".format(len(cnts)))
show_images([allContourImage], ["All contours from edge detected image"])

# finding the document contour
if len(cnts) > 0:
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)

    for c in cnts:
        peri = cv2.arcLength(c, closed=True)
        approx = cv2.approxPolyDP(c, epsilon=peri*0.02, closed=True)

        if len(approx) == 4:
            docCnt = approx
            break

contourImage = image.copy()
cv2.drawContours(contourImage, [docCnt], -1, (0, 0, 255), 2)
show_images([contourImage], ["Outline"])


# Getting the bird's eye view, top-view of the document
paper = four_point_transform(image, docCnt.reshape(4, 2))
warped = four_point_transform(gray, docCnt.reshape(4, 2))
show_images([paper, warped], ["Paper", "Gray"])


# Thresholding the document
thresh = cv2.threshold(warped, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
show_images([thresh], ["Thresh"])


# Finding contours in threshold image
cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
cnts = imutils.grab_contours(cnts)
print("Total contours found after threshold {}".format(len(cnts)))
questionCnts = []

allContourImage = paper.copy()
cv2.drawContours(allContourImage, cnts, -1, (0, 0, 255), 3)
show_images([allContourImage], ["All contours from threshold image"])

# Finding the questions contours
for c in cnts:
    (x, y, w, h) = cv2.boundingRect(c)
    ar = w / float(h)

    if w >= 20 and h >= 20 and ar >= 0.9 and ar <= 1.1:
        questionCnts.append(c)

print("Total questions contours found: {}".format(len(questionCnts)))

questionsContourImage = paper.copy()
cv2.drawContours(questionsContourImage, questionCnts, -1, (0, 0, 255), 3)
show_images([questionsContourImage], ["All questions contours after filtering questions"])

# Sorting the contours according to the question
questionCnts = contours.sort_contours(questionCnts, method="top-to-bottom")[0]
correct = 0
questionsContourImage = paper.copy()

for (q, i) in enumerate(np.arange(0, len(questionCnts), 5)):
    cnts = contours.sort_contours(questionCnts[i: i+5])[0]
    cv2.drawContours(questionsContourImage, cnts, -1, (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), 2)
    bubbled = None

    for (j, c) in enumerate(cnts):
        mask = np.zeros(thresh.shape, dtype="uint8")
        cv2.drawContours(mask, [c], -1, 255, -1)

        mask = cv2.bitwise_and(thresh, thresh, mask=mask)
        show_images([mask], ["Mask of question {} for row {}".format(j+1, q+1)])
        total = cv2.countNonZero(mask)

        if bubbled is None or total > bubbled[0]:
            bubbled = (total, j)

    color = (0, 0, 255)
    k = ANSWER_KEY[q]

    if k == bubbled[1]:
        color = (0, 255, 0)
        correct += 1

    cv2.drawContours(paper, [cnts[k]], -1, color, 3)

show_images([questionsContourImage], ["All questions contours with different colors"])

score = (correct / 5.0) * 100
print("INFO Score: {:.2f}%".format(score))
cv2.putText(paper, "{:.2f}%".format(score), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
show_images([image, paper], ["Original", "exam"])



