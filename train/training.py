"""
Copyright 2020- Kai.Lib
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
      http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import time, torch, random
from train.distance import get_distance
from definition import logger
import pandas as pd

train_step_result = {'loss': [], 'cer': []}
eval_step_result = {'loss': [], 'cer': []}

def train(model, total_batch_size, queue, criterion, optimizer, device, train_begin, train_loader_count, print_batch=5, teacher_forcing_ratio=1):
    total_loss = 0.
    total_num = 0
    total_dist = 0
    total_length = 0
    total_sent_num = 0
    batch = 0

    model.train()
    begin = epoch_begin = time.time()

    while True:
        feats, scripts, feat_lengths, script_lengths = queue.get()
        if feats.shape[0] == 0:
            # empty feats means closing one loader
            train_loader_count -= 1
            logger.debug('left train_loader: %d' % (train_loader_count))

            if train_loader_count == 0:
                break
            else:
                continue
        optimizer.zero_grad()

        feats = feats.to(device)
        scripts = scripts.to(device)
        src_len = scripts.size(1)
        target = scripts[:, 1:]
        model.module.flatten_parameters()

        # Seq2seq forward()
        logit = model(feats, feat_lengths, scripts, teacher_forcing_ratio)

        logit = torch.stack(logit, dim=1).to(device)

        y_hat = logit.max(-1)[1]

        loss = criterion(logit.contiguous().view(-1, logit.size(-1)), target.contiguous().view(-1))
        total_loss += loss.item()
        total_num += sum(feat_lengths)
        display = random.randrange(0, 100) == 0
        dist, length = get_distance(target, y_hat, display=display)
        total_dist += dist
        total_length += length

        total_sent_num += target.size(0)

        loss.backward()
        optimizer.step()

        if batch % print_batch == 0:
            current = time.time()
            elapsed = current - begin
            epoch_elapsed = (current - epoch_begin) / 60.0
            train_elapsed = (current - train_begin) / 3600.0

            logger.info('batch: {:4d}/{:4d}, loss: {:.4f}, cer: {:.2f}, elapsed: {:.2f}s {:.2f}m {:.2f}h'
                .format(batch,
                        total_batch_size,
                        total_loss / total_num,
                        total_dist / total_length,
                        elapsed, epoch_elapsed, train_elapsed))
            begin = time.time()

        if batch % 1000 == 0:
            train_step_result["loss"].append(total_loss / total_num)
            eval_step_result["cer"].append(total_dist / total_length)
            train_df = pd.DataFrame(train_step_result)
            eval_df = pd.DataFrame(eval_step_result)
            train_df.to_csv("./csv/train_step_result.csv", encoding='cp949', index=False)
            eval_df.to_csv("./csv/eval_step_result.csv", encoding='cp949', index=False)

            del train_df
            del eval_df

        batch += 1
        train.cumulative_batch_count += 1

    logger.info('train() completed')
    return total_loss / total_num, total_dist / total_length

train.cumulative_batch_count = 0