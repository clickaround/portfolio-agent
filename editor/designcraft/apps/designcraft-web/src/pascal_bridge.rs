//! Restricted command protocol used by the Pascal workbench.
use serde_json::Value;

const MAX_MESSAGE_BYTES: usize = 65_536;
const ALLOWED: &[&str] = &["frame.create", "text.insert", "edit.undo", "edit.redo", "document.inspect"];

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
    if command == "document.inspect" && !params.as_object().is_some_and(serde_json::Map::is_empty) {
        return Err("inspection does not accept parameters");
    }
    Ok((id.to_owned(), command.to_owned(), params))
}

/// Keep local paths and unrelated editor state out of the parent/model context.
pub fn sanitize_inspection(value: &Value) -> Result<Value, String> {
    let mut safe = serde_json::Map::new();
    for key in ["title", "dirty", "pageCount", "settings", "spreads", "stories", "selection"] {
        if let Some(item) = value.get(key) {
            safe.insert(key.to_owned(), item.clone());
        }
    }
    let result = Value::Object(safe);
    if serde_json::to_vec(&result).map_err(|_| "invalid document snapshot")?.len() > 30_000 {
        return Err("document snapshot exceeds size limit".into());
    }
    Ok(result)
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

    #[test]
    fn inspection_is_read_only_and_does_not_expose_the_document_path() {
        let request = r#"{"type":"pascal-editor-command","id":"1","command":"document.inspect","params":{}}"#;
        assert_eq!(parse_request(request).unwrap().1, "document.inspect");
        assert!(parse_request(&request.replace(r#""params":{}"#, r#""params":{"path":"secret"}"#)).is_err());
        let result = sanitize_inspection(&serde_json::json!({
            "title": "Portfolio", "path": "/private/project.designcraft", "pageCount": 1,
            "dirty": true, "spreads": [], "stories": [], "selection": {}
        }))
        .unwrap();
        assert!(result.get("path").is_none());
        assert_eq!(result["pageCount"], 1);
        assert_eq!(result["dirty"], true);
    }
}
