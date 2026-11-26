use std::fs;
use std::io::Write;
use std::process::{self, Command, Stdio};
use std::thread;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};

#[test]
fn creates_world_directory_and_stops_on_command() {
    let timestamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .expect("system clock is before the Unix epoch")
        .as_nanos();
    let world_dir =
        std::env::temp_dir().join(format!("ferrite server test {} {timestamp}", process::id()));

    let mut child = Command::new(env!("CARGO_BIN_EXE_ferrite-server"))
        .arg("--world-dir")
        .arg(&world_dir)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .expect("start ferrite-server");

    child
        .stdin
        .as_mut()
        .expect("server stdin")
        .write_all(b"stop\n")
        .expect("send stop command");

    // Keep stdin open so the test verifies shutdown on `stop`.
    let deadline = Instant::now() + Duration::from_secs(10);
    while child.try_wait().expect("check server status").is_none() {
        if Instant::now() >= deadline {
            let _ = child.kill();
            let _ = child.wait();
            let _ = fs::remove_dir_all(&world_dir);
            panic!("server did not exit after receiving stop");
        }
        thread::sleep(Duration::from_millis(20));
    }

    let output = child.wait_with_output().expect("read server output");
    let world_created = world_dir.is_dir();
    if world_created {
        fs::remove_dir_all(&world_dir).expect("remove temporary world directory");
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(output.status.success(), "server failed: {stderr}");
    assert!(world_created, "server did not create the world directory");
    assert!(stdout.contains("Server ready."));
    assert!(stdout.contains("Server stopped."));
}
