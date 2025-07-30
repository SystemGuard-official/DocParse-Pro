import streamlit as st
from PIL import Image
import os
import csv
import json
from datetime import datetime
from collections import defaultdict

# Configuration
IMAGE_DIR = "/app/trocr_training/images"
DATA_FILE = "/app/trocr_training/annotations_data.json"

# Data structure: {filename: {users: {user: {text, timestamp, confidence}}, flags: [], bookmarks: [], consensus: text}}
def load_images(image_dir):
    return sorted([f for f in os.listdir(image_dir)
                  if f.lower().endswith(('.jpg', '.png', '.jpeg', '.bmp', '.tiff'))])

def initialize_data(image_files):
    data = {}
    for filename in image_files:
        data[filename] = {
            'users': {},
            'flags': [],
            'bookmarks': [],
            'consensus': '',
            'created': datetime.now().isoformat(),
            'modified': datetime.now().isoformat()
        }
    return data

def load_data(data_file, data):
    if os.path.exists(data_file):
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
                for filename, file_data in loaded_data.items():
                    if filename in data:
                        data[filename].update(file_data)
        except Exception as e:
            st.warning(f"Could not load existing data: {e}")

def save_data(data, data_file):
    try:
        for filename in data:
            data[filename]['modified'] = datetime.now().isoformat()
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"Could not save data: {e}")

def export_to_csv(data, image_files, current_user):
    csv_file = f"/app/trocr_training/images/annotations_{current_user}.csv"
    try:
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["filename", "text", "confidence", "timestamp", "flags", "bookmarked"])
            for filename in image_files:
                file_data = data[filename]
                user_data = file_data['users'].get(current_user, {})
                text = user_data.get('text', '')
                confidence = user_data.get('confidence', '')
                timestamp = user_data.get('timestamp', '')
                flags = ', '.join(file_data.get('flags', []))
                bookmarked = len(file_data.get('bookmarks', [])) > 0
                writer.writerow([filename, text, confidence, timestamp, flags, bookmarked])
    except Exception as e:
        st.warning(f"Could not export CSV: {e}")

def filter_files(data, image_files, current_user, current_filter):
    if current_filter == "all":
        return image_files[:]
    elif current_filter == "annotated":
        return [f for f in image_files
                if current_user in data[f]['users']
                and data[f]['users'][current_user].get('text', '').strip()]
    elif current_filter == "unannotated":
        return [f for f in image_files
                if current_user not in data[f]['users']
                or not data[f]['users'][current_user].get('text', '').strip()]
    elif current_filter == "flagged":
        return [f for f in image_files if data[f].get('flags', [])]
    elif current_filter == "bookmarked":
        return [f for f in image_files if data[f].get('bookmarks', [])]
    elif current_filter == "consensus_needed":
        return [f for f in image_files
                if len(data[f]['users']) > 1 and not data[f].get('consensus', '').strip()]
    else:
        return image_files[:]

def main():
    st.set_page_config("TrOCR Annotation Tool", layout="wide")
    st.title("TrOCR Annotation Tool")

    # Session state init
    if "initialized" not in st.session_state:
        st.session_state.initialized = False
        st.session_state.current_user = ""
        st.session_state.current_filter = "all"
        st.session_state.current_index = 0
        st.session_state.data = {}
        st.session_state.image_files = []
        st.session_state.filtered_files = []
        st.session_state.text_input = ""
        st.session_state.confidence = "high"
        st.session_state.exported_csv = False

    # Login
    if st.session_state.current_user == "":
        username = st.text_input("Enter your username:")
        if st.button("Login") or username:
            if not username.strip():
                st.error("Username required")
            else:
                st.session_state.current_user = username.strip()
                # Load images and data
                st.session_state.image_files = load_images(IMAGE_DIR)
                if not st.session_state.image_files:
                    st.error(f"No images found in {IMAGE_DIR}")
                    return
                st.session_state.data = initialize_data(st.session_state.image_files)
                load_data(DATA_FILE, st.session_state.data)
                st.session_state.filtered_files = filter_files(
                    st.session_state.data, st.session_state.image_files,
                    st.session_state.current_user, st.session_state.current_filter)
                st.session_state.initialized = True
        return

    # Filters
    filter_map = {
        "All Images": "all",
        "Annotated": "annotated",
        "Unannotated": "unannotated",
        "Flagged": "flagged",
        "Bookmarked": "bookmarked",
        "Need Consensus": "consensus_needed"
    }
    filter_display = {v: k for k, v in filter_map.items()}
    filter_options = list(filter_map.keys())
    selected_filter_display = filter_display[st.session_state.current_filter]
    selected_filter = st.selectbox("Filter:", filter_options, index=filter_options.index(selected_filter_display))
    new_filter = filter_map[selected_filter]
    if new_filter != st.session_state.current_filter:
        st.session_state.current_filter = new_filter
        st.session_state.filtered_files = filter_files(
            st.session_state.data, st.session_state.image_files,
            st.session_state.current_user, st.session_state.current_filter)
        st.session_state.current_index = 0

    # Progress and navigation
    total_filtered = len(st.session_state.filtered_files)
    total_images = len(st.session_state.image_files)
    annotated_by_user = sum(1 for fname in st.session_state.image_files
                            if st.session_state.current_user in st.session_state.data[fname]['users']
                            and st.session_state.data[fname]['users'][st.session_state.current_user].get('text', '').strip())
    st.sidebar.info(f"User progress: {annotated_by_user}/{total_images} ({(annotated_by_user/total_images)*100:.1f}%)")
    st.sidebar.info(f"Image {st.session_state.current_index+1} of {total_filtered} (filtered)")

    # Navigation controls
    col1, col2, col3, col4, col5 = st.columns([1,1,1,1,2])
    if col1.button("◀◀ First"):
        st.session_state.current_index = 0
    if col2.button("◀ Prev") and st.session_state.current_index > 0:
        st.session_state.current_index -= 1
    if col3.button("Next ▶") and st.session_state.current_index < total_filtered - 1:
        st.session_state.current_index += 1
    if col4.button("Last ▶▶"):
        st.session_state.current_index = total_filtered - 1
    jump_to = col5.number_input("Go to:", min_value=1, max_value=total_filtered, value=st.session_state.current_index+1)
    if col5.button("Go"):
        st.session_state.current_index = jump_to - 1

    # Show image
    if total_filtered == 0:
        st.warning("No images match the current filter.")
        return

    filename = st.session_state.filtered_files[st.session_state.current_index]
    file_data = st.session_state.data[filename]
    image_path = os.path.join(IMAGE_DIR, filename)

    try:
        img = Image.open(image_path)
        img.thumbnail((700, 400), Image.Resampling.LANCZOS)
        if img.width < 200:
            scale_factor = 200 / img.width
            new_size = (int(img.width * scale_factor), int(img.height * scale_factor))
            img = img.resize(new_size, Image.Resampling.NEAREST)
        st.image(img, caption=filename)
    except Exception as e:
        st.error(f"Error loading image: {e}")

    # Status indicators
    indicators = []
    if st.session_state.current_user in file_data['users'] and file_data['users'][st.session_state.current_user].get('text', '').strip():
        indicators.append(("✅ Annotated", "green"))
    else:
        indicators.append(("❌ Not Annotated", "red"))
    user_count = len(file_data['users'])
    if user_count > 1:
        indicators.append((f"👥 {user_count} users", "blue"))
    if file_data.get('consensus', '').strip():
        indicators.append(("🎯 Consensus", "green"))
    elif user_count > 1:
        indicators.append(("❓ No Consensus", "orange"))
    if file_data.get('flags'):
        indicators.append((f"🚩 {len(file_data['flags'])} flags", "red"))
    if file_data.get('bookmarks'):
        indicators.append((f"🔖 {len(file_data['bookmarks'])} bookmarks", "purple"))
    status_text = " | ".join([f":{color}[{text}]" for text, color in indicators])
    st.info(status_text)

    # Annotation input
    user_data = file_data['users'].get(st.session_state.current_user, {})
    default_text = user_data.get('text', '')
    default_confidence = user_data.get('confidence', 'high')
    st.session_state.text_input = st.text_input("Transcription:", value=default_text)
    st.session_state.confidence = st.selectbox("Confidence:", ["low", "medium", "high"], index=["low", "medium", "high"].index(default_confidence))

    col6, col7, col8, col9 = st.columns([2,2,2,2])
    if col6.button("Save Current"):
        if st.session_state.current_user not in file_data['users']:
            file_data['users'][st.session_state.current_user] = {}
        file_data['users'][st.session_state.current_user].update({
            'text': st.session_state.text_input.strip(),
            'confidence': st.session_state.confidence,
            'timestamp': datetime.now().isoformat()
        })
        save_data(st.session_state.data, DATA_FILE)
        export_to_csv(st.session_state.data, st.session_state.image_files, st.session_state.current_user)
        st.success(f"Saved annotation for {filename}.")

    if col7.button("Save & Next"):
        if st.session_state.current_user not in file_data['users']:
            file_data['users'][st.session_state.current_user] = {}
        file_data['users'][st.session_state.current_user].update({
            'text': st.session_state.text_input.strip(),
            'confidence': st.session_state.confidence,
            'timestamp': datetime.now().isoformat()
        })
        save_data(st.session_state.data, DATA_FILE)
        export_to_csv(st.session_state.data, st.session_state.image_files, st.session_state.current_user)
        st.success(f"Saved annotation for {filename}.")
        if st.session_state.current_index < total_filtered - 1:
            st.session_state.current_index += 1

    if col8.button("Skip"):
        if st.session_state.current_index < total_filtered - 1:
            st.session_state.current_index += 1

    if col9.button("Clear Text"):
        st.session_state.text_input = ""

    # Flags & bookmarks
    colA, colB, colC = st.columns([1,1,2])
    def toggle_flag():
        flag_entry = f"{st.session_state.current_user}"
        flag_exists = any(f.startswith(st.session_state.current_user) for f in file_data['flags'])
        if not flag_exists:
            reason = st.text_input("Reason for flagging (optional):", key=f"flag_reason_{filename}")
            if st.button("Confirm Flag", key=f"confirm_flag_{filename}"):
                entry = f"{st.session_state.current_user}: {reason.strip()}" if reason.strip() else st.session_state.current_user
                file_data['flags'].append(entry)
                save_data(st.session_state.data, DATA_FILE)
                st.experimental_rerun()
        else:
            file_data['flags'] = [f for f in file_data['flags']
                                  if not f.startswith(st.session_state.current_user)]
            save_data(st.session_state.data, DATA_FILE)
            st.experimental_rerun()

    if colA.button("🚩 Flag/Unflag"):
        toggle_flag()

    def toggle_bookmark():
        if st.session_state.current_user not in file_data['bookmarks']:
            file_data['bookmarks'].append(st.session_state.current_user)
        else:
            file_data['bookmarks'].remove(st.session_state.current_user)
        save_data(st.session_state.data, DATA_FILE)
        st.experimental_rerun()

    if colB.button("🔖 Bookmark/Unbookmark"):
        toggle_bookmark()

    # Multi-user info and consensus
    with st.expander("Multi-User Info & Consensus", expanded=True):
        if file_data['users']:
            st.markdown("**User Annotations:**")
            for user, user_data in file_data['users'].items():
                confidence = user_data.get('confidence', 'unknown')
                text = user_data.get('text', '')
                timestamp = user_data.get('timestamp', '')
                st.write(f"- **{user}** [{confidence}] {text if text else '(no annotation)'} ({timestamp})")

        st.markdown("**Consensus:**")
        if file_data.get('consensus'):
            st.success(file_data['consensus'])
        else:
            st.warning("No consensus set")
        if len(file_data['users']) > 1:
            consensus_choice = st.radio("Set consensus from user annotations:", [
                f"{user}: {user_data.get('text', '')}" for user, user_data in file_data['users'].items()
            ], key=f"consensus_radio_{filename}")
            custom_consensus = st.text_input("Or enter custom consensus:", key=f"custom_consensus_{filename}")
            if st.button("Save Consensus", key=f"save_consensus_{filename}"):
                consensus_text = custom_consensus.strip() or consensus_choice.split(": ", 1)[-1]
                if consensus_text:
                    file_data['consensus'] = consensus_text
                    save_data(st.session_state.data, DATA_FILE)
                    st.success("Consensus saved!")
                    st.experimental_rerun()
                else:
                    st.warning("Please select or enter consensus text.")

        if file_data.get('flags'):
            st.markdown("**Flags:**")
            for flag in file_data['flags']:
                st.write(f"- 🚩 {flag}")
        if file_data.get('bookmarks'):
            st.markdown("**Bookmarks:**")
            for bookmark in file_data['bookmarks']:
                st.write(f"- 🔖 {bookmark}")

    # Export CSV option
    if st.button("Export My Annotations to CSV"):
        export_to_csv(st.session_state.data, st.session_state.image_files, st.session_state.current_user)
        st.session_state.exported_csv = True
    if st.session_state.exported_csv:
        csv_path = f"/app/trocr_training/images/annotations_{st.session_state.current_user}.csv"
        if os.path.exists(csv_path):
            with open(csv_path, "rb") as f:
                st.download_button("Download CSV", data=f, file_name=f"annotations_{st.session_state.current_user}.csv", mime="text/csv")

    # Switch user
    if st.sidebar.button("Switch User"):
        st.session_state.current_user = ""
        st.session_state.initialized = False
        st.experimental_rerun()

if __name__ == "__main__":
    main()
# streamlit run annotation_tool\data_annoation_streamlit.py --server.port 8001
