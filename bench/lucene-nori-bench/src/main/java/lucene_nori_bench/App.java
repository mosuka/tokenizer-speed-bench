package lucene_nori_bench;

import java.io.BufferedWriter;
import java.io.IOException;
import java.io.StringReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Scanner;
import org.apache.lucene.analysis.TokenStream;
import org.apache.lucene.analysis.ko.KoreanTokenizer;
import org.apache.lucene.analysis.tokenattributes.OffsetAttribute;

public class App {
    public static void main(String[] args) throws IOException {
        // DecompoundMode.NONE emits dictionary entries whole, like the alyze
        // and lindera ko-dic rows; Lucene's default is DecompoundMode.DISCARD.
        // No unigrams for unknown words, and punctuation is discarded, which
        // are the defaults.
        KoreanTokenizer tokenizer = new KoreanTokenizer(TokenStream.DEFAULT_TOKEN_ATTRIBUTE_FACTORY, null,
                KoreanTokenizer.DecompoundMode.NONE, false, true);
        Scanner input = new Scanner(System.in, "utf-8");
        List<String> lines = new ArrayList<String>();
        while (input.hasNext()) {
            lines.add(input.nextLine());
        }
        Instant start = Instant.now();
        int n_words = 0;
        for (String line : lines) {
            // One tokenizer is reused for every line, as Lucene intends.
            tokenizer.setReader(new StringReader(line));
            tokenizer.reset();
            while (tokenizer.incrementToken()) {
                n_words++;
            }
            tokenizer.end();
            tokenizer.close();
        }
        Instant finish = Instant.now();
        double timeElapsed = (double) Duration.between(start, finish).toNanos() / 1000000000;
        System.out.println("Elapsed-lucene-nori: " + timeElapsed + " [sec]");
        System.out.println(n_words);

        // With BENCH_TOKENS=<file>, write the tokens of every line after the
        // timed loop, one per line with an empty line after each input line,
        // for segmentation.py. The timed loop above is unchanged.
        String path = System.getenv("BENCH_TOKENS");
        if (path != null) {
            OffsetAttribute offset = tokenizer.addAttribute(OffsetAttribute.class);
            try (BufferedWriter out = Files.newBufferedWriter(Paths.get(path), StandardCharsets.UTF_8)) {
                for (String line : lines) {
                    tokenizer.setReader(new StringReader(line));
                    tokenizer.reset();
                    while (tokenizer.incrementToken()) {
                        out.write(line, offset.startOffset(), offset.endOffset() - offset.startOffset());
                        out.write('\n');
                    }
                    tokenizer.end();
                    tokenizer.close();
                    out.write('\n');
                }
            }
        }
    }
}
