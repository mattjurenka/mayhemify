#![no_main]
use libfuzzer_sys::fuzz_target;

// TODO: add docs about arbitrary
fuzz_target!(|value: &[u8]| {
    // TODO: add docs about how to fuzz
});
