use std::io::BufRead;
use std::io::Write;

use alyze::cjk::smartcn::{self, Options};

fn main() {
    let mut lines = vec![];
    for line in std::io::stdin().lock().lines() {
        lines.push(line.unwrap());
    }

    // smartcn has no options yet. It always emits punctuation, as a "," token
    // of kind Punctuation; every token is counted. The scratch buffer for
    // normalized token text is reused across lines, as alyze intends.
    let mut buffer = String::new();

    let mut n_words = 0;
    let start = std::time::Instant::now();
    for line in &lines {
        smartcn::tokenize(line, Options::default(), &mut buffer, |_token| {
            n_words += 1;
            true
        });
    }
    let duration = start.elapsed();

    println!("Elapsed-alyze-smartcn: {} [sec]", duration.as_secs_f64());
    dbg!(n_words);

    // With BENCH_TOKENS=<file>, write the tokens of every line after the timed
    // loop, one per line with an empty line after each input line, for
    // segmentation.py. The timed loop above is unchanged.
    if let Ok(path) = std::env::var("BENCH_TOKENS") {
        let mut out = std::io::BufWriter::new(std::fs::File::create(path).unwrap());
        for line in &lines {
            smartcn::tokenize(line, Options::default(), &mut buffer, |token| {
                writeln!(out, "{}", &line[token.byte_range.clone()]).unwrap();
                true
            });
            writeln!(out).unwrap();
        }
    }
}
