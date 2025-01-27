# Document Tampering Detection

## Overview

This project aims to detect document tampering using a computer vision model hosted on Amazon SageMaker. The model takes a testing image as input and generates a likelihood prediction of forgery as its output.

To illustrate image forgery detection, we employ the Error Level Analysis (ELA) algorithm. ELA identifies discrepancies in compression levels within an image, operating under the assumption that input images are in JPEG format, which is known for its lossy compression.

While ELA is a powerful technique, it has limitations in detecting certain subtle manipulations. Future work could enhance the model by incorporating additional forensic techniques and leveraging larger, more diverse datasets. This project showcases how deep learning and AWS services can be used to build impactful solutions that boost efficiency, reduce risk, and prevent fraud.

## Getting Started

### Prerequisites

Before you begin, ensure you have the following:

- An AWS account
- Access to Amazon SageMaker
- Basic knowledge of Python and deep learning

### Cloning the Repository

To get started, clone this repository into your Amazon SageMaker Studio environment:

```bash
git clone <repository-url>
cd <repository-directory>
