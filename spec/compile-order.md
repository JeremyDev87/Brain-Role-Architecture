# Compile order

Every instance declares P0-P6 exactly once. P0 compiles first. A layer compiles only after all declared
dependencies. An order can differ from numeric P order; the minimal example compiles P6 before P5.
