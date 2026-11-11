use std::io::BufRead;

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
}
