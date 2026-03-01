|ID|Question|Expected_Output|Actual_Output|is_correct|Notes|
|---|---|---|---|---|---|
|Q1|Use van't Hoff equation. For N2O4(g) ⇌ 2NO2(g), K1=0.30 at 298 K and ΔH°=+57.2 kJ/mol (assume constant). Compute K2 at 308 K. Output only a number rounded to 2 decimals.|0.63|0.30|False|mismatch (expected: '0.63')|
|Q2|Van't Hoff osmotic pressure: i=2, M=0.15 mol/L, T=298 K, R=0.082057 L·atm·mol^-1·K^-1. Compute π in atm. Output only a number rounded to 2 decimals.|7.34|0.03|False|mismatch (expected: '7.34')|
|Q3|Biostatistics: Treatment event rate is 12/150; control event rate is 30/150. Compute relative risk (treatment/control). Output only a number rounded to 2 decimals.|0.40|0.40|True|matched expected output|
|Q4|Biostatistics Bayes task: prevalence=0.02, sensitivity=0.90, specificity=0.95. Compute positive predictive value. Output only a number rounded to 2 decimals.|0.27|0.95|False|mismatch (expected: '0.27')|
|Q5|Given TP=42, FP=18, FN=8, compute F1 = 2TP/(2TP+FP+FN). Output only a number rounded to 3 decimals.|0.764|0.67|False|mismatch (expected: '0.764')|
|Q6|Combinatorial game (Nim variant): one heap has 17 stones, each move removes 1 to 3 stones, normal play. What is the optimal first move? Output only 'remove 1', 'remove 2', or 'remove 3'.|remove 1|remove 1|True|matched expected output|
|Q7|Normal-play Nim with heaps (3,4,5). Give one winning first-move resulting heap triple in parentheses with commas and no spaces. Output only the triple.|(1,4,5)|(3,4,5)|False|mismatch (expected: '(1,4,5)')|
|Q8|Explain in at most 12 words why xor-sum 0 is losing in normal-play Nim. Output one sentence only.|Any move makes xor nonzero, so the opponent can restore zero.|In normal-Play Nim, the xor-sum of 0 is losing because it means that all piles are empty, and the player who makes the last move loses.|False|mismatch (expected: 'Any move makes xor nonzero, so the opponent can restore zero.')|
|Q9|Statistics: If probability p=0.8, compute log-odds ln(p/(1-p)). Output only a number rounded to 3 decimals.|1.386|0.693|False|mismatch (expected: '1.386')|
|Q10|Hardy-Weinberg: if recessive allele frequency q=0.20, what is carrier frequency 2pq? Output only a number rounded to 2 decimals.|0.32|0.80|False|mismatch (expected: '0.32')|
