use std::io::BufRead;
use std::path::Path;

use litsea::language::Language;
use litsea::perceptron::AveragedPerceptron;
use litsea::segmenter::Segmenter;

fn main() {
    let mut pos_learner = AveragedPerceptron::new();
    pos_learner
        .load_model_from_path(Path::new(concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/japanese_pos.model"
        )))
        .unwrap();
    let segmenter = Segmenter::with_pos_learner(Language::Japanese, pos_learner);

    let lines: Vec<_> = std::io::stdin()
        .lock()
        .lines()
        .map(|line| line.unwrap())
        .collect();
    let mut n_words = 0;

    let start = std::time::Instant::now();
    for line in &lines {
        n_words += segmenter.segment_with_pos(line).len();
    }
    let duration = start.elapsed();

    println!(
        "Elapsed-litsea-japanese-pos: {} [sec]",
        duration.as_secs_f64()
    );

    dbg!(n_words);
}
