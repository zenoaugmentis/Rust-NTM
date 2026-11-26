use std::env;
use std::fs;
use std::io::{self, BufRead};
use std::path::PathBuf;
use std::process::ExitCode;

fn main() -> ExitCode {
    let mut args = env::args_os().skip(1);
    let world_dir = match (args.next(), args.next(), args.next()) {
        (Some(flag), Some(path), None) if flag == "--world-dir" && !path.is_empty() => {
            PathBuf::from(path)
        }
        _ => {
            eprintln!("Usage: ferrite-server --world-dir <path>");
            return ExitCode::FAILURE;
        }
    };

    if let Err(error) = run(world_dir) {
        eprintln!("ferrite-server: {error}");
        return ExitCode::FAILURE;
    }

    ExitCode::SUCCESS
}

fn run(world_dir: PathBuf) -> io::Result<()> {
    fs::create_dir_all(&world_dir)?;
    println!("Server ready. World directory: {}", world_dir.display());

    for line in io::stdin().lock().lines() {
        if line?.trim() == "stop" {
            break;
        }
    }

    println!("Server stopped.");
    Ok(())
}
