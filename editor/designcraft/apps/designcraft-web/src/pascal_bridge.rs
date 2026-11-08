//! Restricted command protocol used by the Pascal workbench.
use serde_json::Value;

const MAX_MESSAGE_BYTES: usize = 65_536;
const ALLOWED: &[&str] = &["frame.create", "text.insert", "edit.undo", "edit.redo"];

pub fn parse_request(raw: &str) -> Result<(String, String, Value), &'static str> {
    if raw.len() > MAX_MESSAGE_BYTES {
        return Err("request exceeds size limit");
    }
    let value: Value = serde_json::from_str(raw).map_err(|_| "invalid JSON")?;
    if value.get("type").and_then(Value::as_str) != Some("pascal-editor-command") {
        return Err("unsupported request type");
    }
    let id = value.get("id").and_then(Value::as_str).filter(|s| !s.is_empty() && s.len() <= 128).ok_or("invalid request id")?;
    let command = value.get("command").and_then(Value::as_str).filter(|s| ALLOWED.contains(s)).ok_or("command not allowed")?;
    let params = value.get("params").filter(|v| v.is_object()).cloned().ok_or("params must be an object")?;
    Ok((id.to_owned(), command.to_owned(), params))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn permits_only_bounded_edit_commands() {
        let request = r#"{"type":"pascal-editor-command","id":"1","command":"frame.create","params":{"rect":[0,0,50,50]}}"#;
        assert_eq!(parse_request(request).unwrap().1, "frame.create");
        assert!(parse_request(&request.replace("frame.create", "file.open")).is_err());
        assert!(parse_request(&"x".repeat(65_537)).is_err());
        assert!(parse_request(&request.replace("{\"rect\":[0,0,50,50]}", "[]")).is_err());
    }
}
