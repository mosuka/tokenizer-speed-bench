use std::io::BufRead;
use std::io::Write;
use std::path::Path;

use litsea::language::Language;
use litsea::segmenter::Segmenter;
use litsea::two_stage::TwoStageLearner;

fn main() {
    let mut two_stage_learner = TwoStageLearner::new();
    two_stage_learner
        .load_model_from_path(Path::new(concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/english_pos.model"
        )))
        .unwrap();
    let segmenter = Segmenter::with_two_stage_learner(Language::English, two_stage_learner);

    let lines: Vec<_> = std::io::stdin()
        .lock()
        .lines()
        .map(|line| line.unwrap())
        .collect();
    let mut n_words = 0;

    let start = std::time::Instant::now();
    for line in &lines {
        n_words += segmenter.segment_with_pos(line).unwrap().len();
    }
    let duration = start.elapsed();

    println!(
        "Elapsed-litsea-english-two-stage: {} [sec]",
        duration.as_secs_f64()
    );

    dbg!(n_words);

    // With BENCH_TOKENS=<file>, write the tokens of every line after the timed
    // loop, one per line with an empty line after each input line, for
    // segmentation.py. The timed loop above is unchanged.
    if let Ok(path) = std::env::var("BENCH_TOKENS") {
        let mut out = std::io::BufWriter::new(std::fs::File::create(path).unwrap());
        for line in &lines {
            for (token, _) in segmenter.segment_with_pos(line).unwrap() {
                writeln!(out, "{}", token).unwrap();
            }
            writeln!(out).unwrap();
        }
    }
}
