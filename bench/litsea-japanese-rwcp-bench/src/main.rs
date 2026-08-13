use std::io::BufRead;
use std::path::Path;

use litsea::adaboost::AdaBoost;
use litsea::language::Language;
use litsea::segmenter::Segmenter;

fn main() {
    let mut learner = AdaBoost::new(0.01, 100);
    learner
        .load_model_from_path(Path::new(concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/RWCP.model"
        )))
        .unwrap();
    let segmenter = Segmenter::with_learner(Language::Japanese, learner);

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

    println!(
        "Elapsed-litsea-japanese-rwcp: {} [sec]",
        duration.as_secs_f64()
    );

    dbg!(n_words);
}
