# V1 Target Definition

V1 will NOT initially define irrigation need from a
machine-learning label alone.

Candidate target hierarchy:

## Tier A — strongest target

Actual irrigation delivery / farmer irrigation event

Examples:
- irrigation records
- water delivered to farm units
- irrigation scheduling records

## Tier B

Measured crop-water deficit based on:

ETc
- effective rainfall
- soil-water availability

## Tier C

Remote-sensing-supported irrigation deficit using:

- actual ET
- reference ET
- vegetation state
- soil moisture
- precipitation

## Tier D — proxy only

Low soil moisture + high evaporative demand +
vegetation deterioration

Tier D should only be used if stronger ground truth
cannot be obtained.

## Rule

Do not claim "irrigation need" unless the label has a
clear physical or operational interpretation.
