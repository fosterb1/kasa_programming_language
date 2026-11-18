# Learn Kasa — first programs and challenges

Kasa is a Twi-first language. Programs are saved in UTF-8 `.kasa` files. You
can run them in the [Playground](../playground/) or use `kasa-native run`.
Its current vocabulary is provisional and should undergo community review.

## Lesson 1: Talk to the computer

```kasa
ka "Maakye, Ghana!"
```

`ka` displays a value. Try changing the message.

## Lesson 2: Variables and calculations

```kasa
ma ɛdin = "Akosua"
ma sika = 125
ka "Maakye, " + ɛdin
ka sika * 4
```

`ma` creates or changes a name. You must use `nsɛm()` to convert numbers
before joining them with text.

## Lesson 3: Decisions

```kasa
ma mfe = 16
sɛ mfe >= 18 a
    ka "Adult"
anyɛ_saa_a
    ka "Young"
awiei
```

The `a` after the condition and `awiei` ending the block are required. Try
changing the age to 20.

## Lesson 4: Repetition

```kasa
mpɛn 3
    ka "Meda wo ase"
awiei
```

For a variable number of repetitions, use `bere_a` and make sure your loop
condition eventually becomes false.

## Lesson 5: Functions and lists

```kasa
dwumadie fa_bi(a, b)
    sanma a + b
awiei

ma scores = [80, 90, 70]
ka fa_bi(scores[0], scores[1])
ka tentɛn(scores)
```

List positions start at zero. `sanma` returns a value from a function.

## Lesson 6: Real projects (15 runnable examples)

The [`examples/`](../examples/) directory includes **15 runnable Kasa files**:

| Example | What you learn |
| --- | --- |
| `hello.kasa` | Print text |
| `conditions.kasa` | If / else |
| `loops.kasa` | While and counted loops |
| `functions.kasa` | Function arguments and return |
| `lists.kasa` | Indexing and mutation |
| `factorial.kasa` | Recursion |
| `fibonacci.kasa` | Repeated state updates |
| `multiplication_table.kasa` | Iteration and formatting |
| `savings_goal.kasa` | Practical savings model |
| `quiz.kasa` | Boolean decisions |
| `bubble_sort.kasa` | Nested loops and sorting |
| `prime_check.kasa` | Modulo, loops, early exit |
| `grades.kasa` | Aggregation, conditional counters |
| `sales_report.kasa` | Lists and business revenue |
| `number_guess.kasa` | Search and loop break |

**Challenges:** Change the numbers, add more items, alter grade thresholds,
then check whether the output still makes sense. The current language has no
file or network standard library; programs use in-memory data. For input,
`bisa()` reads one line at a time (or the Playground's Input box).
