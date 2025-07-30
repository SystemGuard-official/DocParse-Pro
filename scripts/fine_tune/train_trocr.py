# train_trocr.py

from transformers import (
    TrOCRProcessor,
    VisionEncoderDecoderModel,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    EarlyStoppingCallback
)
import torch
from torch.utils.data import DataLoader
from datasets import load_metric
from prepare_dataset import load_dataset
import evaluate

# Load processor and model
processor = TrOCRProcessor.from_pretrained("microsoft/trocr-large-stage1")
model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-large-stage1")
model.config.decoder_start_token_id = processor.tokenizer.cls_token_id
model.config.pad_token_id = processor.tokenizer.pad_token_id
model.config.vocab_size = model.decoder.config.vocab_size
model.config.max_length = 128
model.config.eos_token_id = processor.tokenizer.eos_token_id

device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)

# Load dataset
dataset = load_dataset("labels.csv")

# Split dataset
split_dataset = dataset.train_test_split(test_size=0.1)
train_dataset = split_dataset["train"]
eval_dataset = split_dataset["test"]

# Preprocessing
def preprocess(example):
    pixel_values = processor(images=example["image"], return_tensors="pt").pixel_values[0]
    labels = processor.tokenizer(
        example["text"], padding="max_length", max_length=128,
        truncation=True, return_tensors="pt"
    ).input_ids[0]
    labels[labels == processor.tokenizer.pad_token_id] = -100  # Mask padding
    return {
        "pixel_values": pixel_values,
        "labels": labels,
    }

train_dataset = train_dataset.map(preprocess, remove_columns=train_dataset.column_names)
eval_dataset = eval_dataset.map(preprocess, remove_columns=eval_dataset.column_names)

# Collator
def collate_fn(batch):
    pixel_values = torch.stack([x["pixel_values"] for x in batch])
    labels = torch.stack([x["labels"] for x in batch])
    return {"pixel_values": pixel_values, "labels": labels}

# Metric
cer_metric = evaluate.load("cer")

def compute_metrics(pred):
    pred_ids = pred.predictions
    label_ids = pred.label_ids
    pred_text = processor.batch_decode(pred_ids, skip_special_tokens=True)
    label_ids[label_ids == -100] = processor.tokenizer.pad_token_id
    label_text = processor.batch_decode(label_ids, skip_special_tokens=True)
    cer = cer_metric.compute(predictions=pred_text, references=label_text)
    return {"cer": cer}

# Training Arguments
training_args = Seq2SeqTrainingArguments(
    output_dir="./trocr-finetuned",
    evaluation_strategy="steps",
    per_device_train_batch_size=2,
    per_device_eval_batch_size=2,
    save_total_limit=2,
    eval_steps=200,
    logging_steps=100,
    learning_rate=5e-5,
    num_train_epochs=10,
    save_strategy="steps",
    save_steps=200,
    predict_with_generate=True,
    load_best_model_at_end=True,
    metric_for_best_model="cer",
    greater_is_better=False,
    fp16=True if torch.cuda.is_available() else False,
)

# Trainer
trainer = Seq2SeqTrainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    tokenizer=processor,
    data_collator=collate_fn,
    compute_metrics=compute_metrics,
    callbacks=[EarlyStoppingCallback(early_stopping_patience=3)],
)

# Start Training
trainer.train()

# Save final model
model.save_pretrained("./trocr-finetuned/best_model")
processor.save_pretrained("./trocr-finetuned/best_model")
