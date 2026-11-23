use std::io::BufRead;
use std::io::Write;
use std::path::Path;

use litsea::adaboost::AdaBoost;
use litsea::language::Language;
use litsea::segmenter::Segmenter;

fn main() {
    let mut learner = AdaBoost::new(0.01, 100);
    learner
        .load_model_from_path(Path::new(concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/korean.model"
        )))
        .unwrap();
    let segmenter = Segmenter::with_learner(Language::Korean, learner);

    let lines: Vec<_> = std::io::stdin()
        .lock()
        .lines()
        .map(|line| line.unwrap())
        .collect();
    let mut n_words = 0;

    let start = std::time::Instant::now();
    for line in &lines {
        n_words += segmenter.segment(line).len();
    }
    let duration = start.elapsed();

    println!("Elapsed-litsea-korean: {} [sec]", duration.as_secs_f64());

    dbg!(n_words);

    // With BENCH_TOKENS=<file>, write the tokens of every line after the timed
    // loop, one per line with an empty line after each input line, for
    // segmentation.py. The timed loop above is unchanged.
    if let Ok(path) = std::env::var("BENCH_TOKENS") {
        let mut out = std::io::BufWriter::new(std::fs::File::create(path).unwrap());
        for line in &lines {
            for token in segmenter.segment(line) {
                writeln!(out, "{}", token).unwrap();
            }
            writeln!(out).unwrap();
        }
    }
}
