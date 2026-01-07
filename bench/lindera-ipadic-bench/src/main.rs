use std::io::BufRead;

use lindera::dictionary::load_dictionary;
use lindera::mode::Mode;
use lindera::segmenter::Segmenter;

fn main() {
    let dictionary = load_dictionary("embedded://ipadic").unwrap();

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
    println!("Elapsed-lindera-ipadic: {} [sec]", duration.as_secs_f64());

    dbg!(n_words);
}
