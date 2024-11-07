# instruction for the AI model to instruct the robot

generate the JSON instruction for a robot which is using the instructions with the structure like in the below example:
<example>
{
 "steps": "directions"
}
</example>

- The robot only knows the direactions like: UP, RIGHT, DOWN, LEFT

- Response should be only the JSON without any comments, additions and other things

- Steps that will guide the robot to the target are: 2*UP, 2*RIGHT, 2*DOWN, 3*RIGHT

# or

generate the JSON instruction for a robot which is using the instructions with the structure like in the below example:
<example>
{
 "steps": "directions"
}
</example>

- The robot only knows the directions like: UP, RIGHT, DOWN, LEFT

- The robot is on the rectangle map that is divided into squares 6*4

- Starting point of the robot is bottom-left corner

- The target is in the bottom-right corner

- The response should only be the JSON without any comments, additions and other things