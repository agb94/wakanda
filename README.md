# wakanda

## What is this tool for?
Wakanda is a tool that automatically generates test data for python functions.

- [Idea Pitching](https://docs.google.com/presentation/d/1dwXjVG7EZPdVwyf-Sq6OzR8X9T0t5ikjcxqLYsk4RAQ/edit?usp=sharing)
- [Presentation Slide](https://docs.google.com/presentation/d/1iRmCP_75RIqYQPrPJanCdP1vM58Z6dy_SdoepdzB-ec/edit?usp=sharing)

## Contributors
- [Gabin An](https://coinse.kaist.ac.kr/members/gabin/), School of Computing, KAIST
- Jisu Ok, School of Computing, KAIST
- Sungbin Jo, School of Computing, KAIST

## Usage

```
python main.py [target_file] [function_name]
```

## Example

Command:
```bash
$ python main.py python-functions/case4.py case4
```

Output:
```
INPUT GENERATOR for python-functions/case4.py
Start type search.......
6 type candidates found.

Start value search......
1/4 branches have been covered while searching types.
4/4 branches have been covered.

RESULT
1T: (0,)
1F: ('Hello',)
2T: ('Hello',)
2F: ('Hell',)
Done.
============================================
```

Wow!
