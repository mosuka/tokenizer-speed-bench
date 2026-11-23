use std::io::BufRead;
use std::io::Write;

use lindera::dictionary::load_dictionary;
use lindera::mode::Mode;
use lindera::segmenter::Segmenter;

fn main() {
    let dictionary =
        load_dictionary(concat!(env!("CARGO_MANIFEST_DIR"), "/lindera-unidic-csj")).unwrap();

    let segmenter = Segmenter::new(Mode::Normal, dictionary, None);

    let lines: Vec<_> = std::io::stdin()
        .lock()
        .lines()
        .map(|line| line.unwrap())
        .collect();
    let mut n_words = 0;

    let start = std::time::Instant::now();

    for line in &lines {
        let tokens = segmenter.segment(line.into()).unwrap();
        n_words += tokens.len();
    }

    let duration = start.elapsed();
    println!(
        "Elapsed-lindera-unidic-csj: {} [sec]",
        duration.as_secs_f64()
    );

    dbg!(n_words);

    // With BENCH_TOKENS=<file>, write the tokens of every line after the timed
    // loop, one per line with an empty line after each input line, for
    // segmentation.py. The timed loop above is unchanged.
    if let Ok(path) = std::env::var("BENCH_TOKENS") {
        let mut out = std::io::BufWriter::new(std::fs::File::create(path).unwrap());
        for line in &lines {
            for token in segmenter.segment(line.into()).unwrap() {
                writeln!(out, "{}", &line[token.byte_start..token.byte_end]).unwrap();
            }
            writeln!(out).unwrap();
        }
    }
}
