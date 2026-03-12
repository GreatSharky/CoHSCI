
# Collaborative Hand Signal Control Interface

## Introduction
This repository hosts the codes for my Master Thesis of science project. The compelte Master thesis is available for download at [Tampere University Trepo](https://trepo.tuni.fi/handle/10024/234478). The thesis is
titled Reliable and Configurable Human–Robot Collaboration Framework Based on Hand Gesture Recognition Using Emoji-Guided Vision-Language Models.
___
## Thesis Abstract

The Industry 5.0 paradigm emphasizes human-centric, sustainable, and resilient industrial systems to reduce the problems of current industrial paradigms. Human–Robot Collaboration (HRC) where human and a robot operate in tandem is a key enabler of the Industry 5.0 paradigm. While collaborative robots are increasingly deployed in manufacturing, current HRC solutions often lack adaptability and require operators to conform to rigid interaction models. Recent advances in artificial intelligence, particularly Vision-Language Models (VLMs), offer new possibilities for creating more intuitive and human-centric collaboration by enabling robots to perceive, interpret, and respond to human actions in a flexible manner. This allows for the robot to adapt to the behavior or preferences of the operator instead of vice versa.  
  
This thesis investigates the integration of a Vision-Language Model into a human–robot collaboration system to enhance collaborative manufacturing task. A modular and configurable framework is proposed in which hand gesture recognition, emoji-based reasoning and robot control are combined into a unified system architecture. The framework is implemented using a locally executed VLM and integrated with a collaborative robot to support a shared assembly task. The system enables multimodal interaction through hand signal input allowing the robot to adapt its behavior based on the operator’s actions and preferences.  
  
The proposed system is evaluated through an experiment-based user study focusing on efficiency, reliability, and user experience. The results indicate that integrating a Vision-Language Model can improve task understanding and flexibility in HRC while maintaining safe operation. Furthermore, user feedback suggests increased performance and improved perceived collaboration compared to conventional interaction methods. The findings demonstrate the potential of Vision-Language Models to support more adaptive and human-centric human–robot collaboration systems in industrial environments.
___ 
## How to use
To run the CoHSCI system following requirements must be setup:
1. Install [Ollama](https://ollama.com/)
2. Run `Ollama pull gemma3:12b`
3. Install [RabbitMQ](https://www.rabbitmq.com/docs/download) following RabbitMQ documentation
4. Install Python 3.12
5. Clone this repository and run `pip install requirements`
6. In `src/settings/config` specify the emojis you want to use to control the robot.
7. Start every module in specific terminal
---
## Future improvements
In future I want to improve the code base. The version used for the thesis is tagged v1.0 and is available branch MTH-final. Future improvements will be:
* Docker implementation
* Cleaner code and file structure
* Possible hand recognition model
