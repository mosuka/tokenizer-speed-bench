use std::io::BufRead;
use std::io::Write;

use alyze::uax29::word::{self, Options};

fn main() {
    let mut lines = vec![];
    for line in std::io::stdin().lock().lines() {
        lines.push(line.unwrap());
    }

    // The UAX #29 word tokenizer reports every span between word boundaries,
    // spaces and punctuation included. Only word-like spans are counted; the
    // timed part is the whole scan either way.
    let mut n_words = 0;
    let start = std::time::Instant::now();
    for line in &lines {
        word::tokenize(line, Options::default(), |_end, props| {
            if props.is_word_like() {
                n_words += 1;
            }
            true
        });
    }
    let duration = start.elapsed();

    println!("Elapsed-alyze-uax29: {} [sec]", duration.as_secs_f64());
    dbg!(n_words);

    // With BENCH_TOKENS=<file>, write the tokens of every line after the timed
    // loop, one per line with an empty line after each input line, for
    // segmentation.py. The timed loop above is unchanged.
    if let Ok(path) = std::env::var("BENCH_TOKENS") {
        let mut out = std::io::BufWriter::new(std::fs::File::create(path).unwrap());
        for line in &lines {
            let mut start = 0;
            word::tokenize(line, Options::default(), |end, props| {
                if props.is_word_like() {
                    writeln!(out, "{}", &line[start..end]).unwrap();
                }
                start = end;
                true
            });
            writeln!(out).unwrap();
        }
    }
}
