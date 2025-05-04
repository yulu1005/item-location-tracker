
import os
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer, DataCollatorForLanguageModeling
from datasets import load_dataset
from peft import LoraConfig, get_peft_model, prepare_model_for_int8_training
import torch

# 路徑設定
model_path = "./gemma-3-1b-it"
data_path = "./intent_data.json"
output_dir = "./lora-gemma3-intent"

# 載入資料集
dataset = load_dataset("json", data_files=data_path, split="train")

# 初始化 tokenizer 和模型
tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=False)
model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float32)

# LoRA 設定
lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.1,
    bias="none",
    task_type="CAUSAL_LM"
)

model = get_peft_model(model, lora_config)

# Tokenize 函數
def tokenize_function(example):
    prompt = example["instruction"] + "\n" + example["input"]
    target = example["output"]
    full_text = prompt + "\n" + target
    tokenized = tokenizer(full_text, truncation=True, max_length=128, padding="max_length")
    tokenized["labels"] = tokenized["input_ids"].copy()
    return tokenized

tokenized_dataset = dataset.map(tokenize_function)

# 訓練參數
training_args = TrainingArguments(
    output_dir=output_dir,
    per_device_train_batch_size=2,
    num_train_epochs=3,
    logging_steps=10,
    save_strategy="epoch",
    learning_rate=2e-4,
    fp16=False,
    bf16=False
)

data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
    tokenizer=tokenizer,
    data_collator=data_collator
)

# 開始訓練
trainer.train()

# 儲存模型
trainer.save_model(output_dir)
