use std::io::BufRead;
use std::path::Path;

use litsea::language::Language;
use litsea::segmenter::Segmenter;
use litsea::two_stage::TwoStageLearner;

fn main() {
    let mut two_stage_learner = TwoStageLearner::new();
    two_stage_learner
        .load_model_from_path(Path::new(concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/japanese_two_stage.model"
        )))
        .unwrap();
    let segmenter = Segmenter::with_two_stage_learner(Language::Japanese, two_stage_learner);

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
        "Elapsed-litsea-japanese-two-stage: {} [sec]",
        duration.as_secs_f64()
    );

    dbg!(n_words);
}
